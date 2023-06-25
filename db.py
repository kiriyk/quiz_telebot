import peewee
import time


class User(peewee.Model):
    id = peewee.PrimaryKeyField()
    username = peewee.CharField()
    created_at = peewee.DateTimeField()
    quiz_completed = peewee.BooleanField()

    class Meta:
        database = peewee.SqliteDatabase('quiz_users.db')


# Добавление пользователя в базу данных
def add_user(username):
    time_now = time.asctime()
    user_exists = User.select().where(User.username == username).exists()
    if not user_exists:
        user = User(username=username, quiz_completed=True, created_at=time_now)
        user.save()


def get_users():
    return User.select()


if __name__ == '__main__':
    User.create_table()
