from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask_sqlalchemy import SQLAlchemy #импортируем класс SQLAlchemy
from datetime import datetime
from flask_admin import Admin #импортируем класс Admin
from flask_admin.contrib.sqla import ModelView #мпорт класса ModelView для регистрации других моделей (Category, Article) в ModelView


app = Flask(__name__)
# 1. Указание пути к БД. config - словарь базы данных. В квадратных скобках - ключ
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#пароль к БД для работы админ-панели
app.config['SECRET_KEY'] = '72715Pass' 
# 2. Cоздание БД. Передаем в класс SQLAlchemy наше веб-приложение Flask
db = SQLAlchemy(app)
#создаем экземпляр класса admin
admin = Admin(app)

#Модель категории статьи
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)
    articles = db.relationship('Article', backref='category_name')

    def __repr__(self):
        return f'Category: {self.id}-{self.name}'


#Модель статьи. Создаем модель в виде класса, унаследованного от модели в базе данных
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True) #primary_key - поле становится первичным ключем
    category_id = db.Column(db.Integer, db.ForeignKey('category.id')) #связь с id конкретной категории. Название класса писать обязательно с маленькой буквы. ForeignKey - внешний ключ
    title = db.Column(db.String(50), nullable=False, unique=True) 
    #50 - количество символов заголовка статьи
    #nullable - может ли заголовок быть пустым, unique - уникальность заголовка
    introduction = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text(), nullable=False)
    pub_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    #магический дандр-метод для вывода статьи как нам надо в терминал
    def __repr__(self):
        return f'Article: {self.id}. {self.title}'


# отправка переменной в html-шаблон
# @ - декоратор. @app - обращение к приложению app. @app.route - передача названия маршрута
@app.route('/base')
def base():   
    return render_template('base.html')


@app.route('/')
def index():
    #.query - это обращение к очереди статей, если их несколько
    #упорядочить по дате публикации и взять последние три статьи с помощью среза
    latest_articles = Article.query.order_by(Article.pub_date.desc())[:3]     
    #создаем переменную с статьями для передачи в шаблон articles
    return render_template('index.html', articles=latest_articles)



@app.route('/blog')
def blog():
    #получим категорию блога
    category = Category.query.filter_by(name='Блог').first()
    #получим очередь статей блога
    articles = Article.query.filter_by(category_id=category.id)

    #после запятой передаем статьи категории Блог в blog.html
    return render_template('blog.html', articles=articles)



@app.route('/news')
def news():
    #здесь передаем статьи рубрики Новости так же, как с блогом
    category = Category.query.filter_by(name='Новости').first()
    articles = Article.query.filter_by(category_id=category.id)
    return render_template('news.html', articles=articles)


@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        category_id = request.form['category_select']
        title = request.form['title']
        introduction = request.form['introduction']
        text = request.form['article_text']

        article = Article(category_id = category_id, 
                          introduction = introduction, 
                          text = text, 
                          title = title)        

        #обработчик ошибок во время добавления статьи
        try:
            db.session.add(article)
            db.session.commit() #подтеврдить
            return redirect(url_for('index')) #после успешного добавления статьи перебросит на главную страницу
        
        except Exception as error:
            return f'Возникла ошибка! -> {error}' #Exception - класс ошибок (указываем его, так как не знаем, какая именно ошибка появится)

    else:
        categories = Category.query.all()
        return render_template('new_post.html', categories = categories)



#детальный просмотр статьи. В адрес передаем аргумент - id этой статьи
@app.route('/detailed_post/<int:article_id>')
def detailed_post(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('detailed.html', article=article)



#маршрут на изменение статьи
@app.route('/edit/<int:article_id>', methods=['GET', 'POST'])
def edit_post(article_id):
    article = Article.query.get_or_404(article_id)
    if request.method == 'POST':
        article.category_id = request.form['category_select']
        article.title = request.form['title']
        article.introduction = request.form['introduction']
        article.text = request.form['article_text']
        
        #исключение если все хорошо
        try:
            db.session.commit()
            return redirect(url_for('index'))
        
        #Exception - большой класс ошибок. Записываем его в переменную error
        except Exception as error: 
            return f'Возникла ошибка при изменении! -> {error}'

    else:        
        categories = Category.query.all()
        return render_template('edit_post.html', article=article, categories = categories)


#удаление статьи
@app.route('/delete/<int:article_id>')
def delete_post(article_id):
    article = Article.query.get_or_404(article_id)

    #попытаемся
    try: 
        db.session.delete(article)
        db.session.commit()
        return redirect(url_for('index'))

    except Exception as error: 
        return f'Возникла ошибка при удалении! -> {error}'
    
#класс для просмотра категории
class CategoryView(ModelView):
    create_modal = True #добавление категории в всплывающем окне
    column_list = ('id', 'name', 'articles')

#регистрируем ModelView для просмотра информации из БД в админ-панели
admin.add_view(CategoryView(Category, db.session))
admin.add_view(ModelView(Article, db.session))


if __name__ == '__main__':
    app.run(debug=True)