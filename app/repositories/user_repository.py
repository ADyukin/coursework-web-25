class UserRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def _row_to_dict(self, row, description):
        if row is None:
            return None
        return {desc[0]: value for desc, value in zip(description, row)}

    def get_by_id(self, user_id):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT * FROM users WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()
            return self._row_to_dict(user, cursor.description)

    def get_by_name(self, name):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT * FROM users WHERE name = %s
            """, (name,))
            user = cursor.fetchone()
            return self._row_to_dict(user, cursor.description)

    def get_by_email(self, email):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT * FROM users WHERE email = %s
            """, (email,))
            user = cursor.fetchone()
            return self._row_to_dict(user, cursor.description)

    def get_by_name_and_password(self, name, password_hash):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT * FROM users WHERE name = %s AND password_hash = %s
            """, (name, password_hash))
            user = cursor.fetchone()
            return self._row_to_dict(user, cursor.description)

    def all(self):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            return [self._row_to_dict(user, cursor.description) for user in users]
    
    def create(self, name, email, password_hash, role='buyer'):
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
            """, (name, email, password_hash, role))
            connection.commit()

    def update(self, user_id, name, email, role=None):
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET name = %s, email = %s, role = %s
                WHERE id = %s
            """, (name, email, role, user_id))
            connection.commit()

    def update_password(self, user_id, password_hash):
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s
                WHERE id = %s
            """, (password_hash, user_id))
            connection.commit()

    def delete(self, user_id):
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            connection.commit()
            return cursor.rowcount > 0

    def get_all_roles(self):
        return [
            ('buyer', 'Покупатель'),
            ('author', 'Автор'),
            ('admin', 'Администратор')
        ]