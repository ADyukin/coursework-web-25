import os
import random

class GameRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector
        self.upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads', 'games')
        self.image_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads', 'images')

    def _row_to_dict(self, row, description):
        if row is None:
            return None
        return {desc[0]: value for desc, value in zip(description, row)}

    def delete_game_files(self, game):
        """Удаляет файлы игры с сервера"""
        if game['file_path']:
            file_path = os.path.join(self.upload_folder, game['file_path'])
            if os.path.exists(file_path):
                os.remove(file_path)
        
        if game['image_url'] and game['image_url'].startswith('images/'):
            image_path = os.path.join(self.image_folder, game['image_url'].split('/')[-1])
            if os.path.exists(image_path):
                os.remove(image_path)

    def get_by_id(self, game_id):
        """Получает игру по ID"""
        with self.db_connector.connect().cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT g.*, u.name as author_name, gn.name as genre_name
                FROM games g
                LEFT JOIN genres gn ON g.genre_id = gn.id
                LEFT JOIN users u ON g.author_id = u.id
                WHERE g.id = %s
            """, (game_id,))
            return cursor.fetchone()

    def get_all(self):
        """Получает все игры"""
        with self.db_connector.connect().cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT g.*, u.name as author_name
                FROM games g
                LEFT JOIN users u ON g.author_id = u.id
                ORDER BY g.created_at DESC
            """)
            return cursor.fetchall()

    def get_all_approved(self):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT 
                    g.id, g.title, g.description, g.system_requirements, g.price, g.genre_id, 
                    g.file_path, g.image_url, g.created_at, g.status,
                    u.name as author_name, u.id as author_id
                FROM games g
                LEFT JOIN users u ON g.author_id = u.id
                WHERE g.status = 'approved'
                ORDER BY g.created_at DESC
            """)
            games = cursor.fetchall()
            return [self._row_to_dict(game, cursor.description) for game in games]

    def get_pending_games(self):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT 
                    g.id, g.title, g.description, g.system_requirements, g.price, g.genre_id, 
                    g.file_path, g.image_url, g.created_at, g.status,
                    u.name as author_name, u.id as author_id
                FROM games g
                LEFT JOIN users u ON g.author_id = u.id
                WHERE g.status = 'pending'
                ORDER BY g.created_at DESC
            """)
            games = cursor.fetchall()
            return [self._row_to_dict(game, cursor.description) for game in games]

    def get_by_author(self, author_id):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT 
                    g.id, g.title, g.description, g.system_requirements, g.price, g.genre_id, 
                    g.file_path, g.image_url, g.created_at, g.status,
                    u.name as author_name, u.id as author_id
                FROM games g
                LEFT JOIN users u ON g.author_id = u.id
                WHERE g.author_id = %s
                ORDER BY g.created_at DESC
            """, (author_id,))
            games = cursor.fetchall()
            return [self._row_to_dict(game, cursor.description) for game in games]

    def get_purchased_games(self, user_id):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT 
                    g.id, g.title, g.description, g.system_requirements, g.price, g.genre_id, 
                    g.file_path, g.image_url, g.created_at, g.status,
                    u.name as author_name, u.id as author_id
                FROM games g
                LEFT JOIN users u ON g.author_id = u.id
                INNER JOIN order_items oi ON g.id = oi.game_id
                INNER JOIN orders o ON oi.order_id = o.id
                WHERE o.buyer_id = %s AND o.status = 'paid'
                ORDER BY g.created_at DESC
            """, (user_id,))
            games = cursor.fetchall()
            return [self._row_to_dict(game, cursor.description) for game in games]

    def is_game_purchased(self, game_id, user_id):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT 1 
                FROM order_items oi
                INNER JOIN orders o ON oi.order_id = o.id
                WHERE oi.game_id = %s AND o.buyer_id = %s AND o.status = 'paid'
            """, (game_id, user_id))
            return cursor.fetchone() is not None

    def create(self, title, description, price, genre_id, author_id, file_path=None, image_url=None, status='pending', system_requirements=None):
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO games (title, description, price, genre_id, author_id, file_path, image_url, status, system_requirements)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, description, price, genre_id, author_id, file_path, image_url, status, system_requirements))
            connection.commit()

    def update(self, game_id, title, description, price, genre_id, file_path=None, image_url=None, system_requirements=None):
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE games 
                SET title = %s, description = %s, price = %s, genre_id = %s, file_path = %s, image_url = %s, system_requirements = %s
                WHERE id = %s
            """, (title, description, price, genre_id, file_path, image_url, system_requirements, game_id))
            connection.commit()

    def update_status(self, game_id, status):
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE games 
                SET status = %s
                WHERE id = %s
            """, (status, game_id))
            connection.commit()

    def delete(self, game_id):
        # Сначала получаем информацию об игре
        game = self.get_by_id(game_id)
        if game:
            # Удаляем файлы игры
            self.delete_game_files(game)
            # Удаляем запись из базы данных
            connection = self.db_connector.connect()
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM games WHERE id = %s", (game_id,))
                connection.commit()
                return cursor.rowcount > 0
        return False

    def get_all_genres(self):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("SELECT * FROM genres ORDER BY name")
            genres = cursor.fetchall()
            return [self._row_to_dict(genre, cursor.description) for genre in genres]

    def get_filtered_games(self, search_query=None, selected_genres=None, selected_authors=None, min_rating=None):
        with self.db_connector.connect().cursor() as cursor:
            query = """
                SELECT 
                    g.id, g.title, g.description, g.system_requirements, g.price, g.genre_id, 
                    g.file_path, g.image_url, g.created_at, g.status,           
                    u.name as author_name, u.id as author_id
                FROM games g
                LEFT JOIN users u ON g.author_id = u.id
                WHERE g.status = 'approved'
            """
            params = []

            if search_query:
                query += " AND g.title LIKE %s"
                params.append(f'%{search_query}%')

            if selected_genres:
                placeholders = ','.join(['%s'] * len(selected_genres))
                query += f" AND g.genre_id IN ({placeholders})"
                params.extend(selected_genres)

            if selected_authors:
                placeholders = ','.join(['%s'] * len(selected_authors))
                query += f" AND g.author_id IN ({placeholders})"
                params.extend(selected_authors)

            query += " ORDER BY g.created_at DESC"

            cursor.execute(query, params)
            games = cursor.fetchall()
            return [self._row_to_dict(game, cursor.description) for game in games]

    def get_game_rating(self, game_id):
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COALESCE(AVG(rating), 0) as avg_rating,
                    COUNT(*) as review_count
                FROM reviews
                WHERE game_id = %s
            """, (game_id,))
            result = cursor.fetchone()
            return {
                'avg_rating': float(result[0]),
                'review_count': result[1]
            }

    def get_banner_game(self):
        """Получает случайную игру для баннера"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT id FROM games 
                WHERE status = 'approved'
            """)
            approved_game_ids = [row[0] for row in cursor.fetchall()]
            if approved_game_ids:
                return random.choice(approved_game_ids)
            return None

    def get_popular_games(self):
        """Получает популярные игры (топ-3 по рейтингу)"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT g.*, u.name as author_name,
                       COALESCE(AVG(r.rating), 0) as avg_rating,
                       COUNT(r.id) as review_count,
                       gn.name as genre_name
                FROM games g
                LEFT JOIN users u ON g.author_id = u.id
                LEFT JOIN reviews r ON g.id = r.game_id
                LEFT JOIN genres gn ON g.genre_id = gn.id
                WHERE g.status = 'approved'
                GROUP BY g.id, u.name, gn.name
                HAVING COUNT(r.id) > 0  -- Только игры с отзывами
                ORDER BY avg_rating DESC, review_count DESC
                LIMIT 3
            """)
            return [dict(zip([column[0] for column in cursor.description], row)) 
                   for row in cursor.fetchall()]

    def get_free_games(self):
        """Получает случайные бесплатные игры"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT g.*, u.name as author_name,
                       COALESCE(AVG(r.rating), 0) as avg_rating,
                       COUNT(r.id) as review_count,
                       gn.name as genre_name
                FROM games g
                LEFT JOIN users u ON g.author_id = u.id
                LEFT JOIN reviews r ON g.id = r.game_id
                LEFT JOIN genres gn ON g.genre_id = gn.id
                WHERE g.status = 'approved' 
                AND g.price = 0  -- Только бесплатные игры
                GROUP BY g.id, u.name, gn.name
                ORDER BY RAND()
                LIMIT 3
            """)
            return [dict(zip([column[0] for column in cursor.description], row)) 
                   for row in cursor.fetchall()]

    def get_genres_with_count(self):
        """Получает жанры с количеством игр"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT g.id, g.name, COUNT(gm.id) as game_count
                FROM genres g
                LEFT JOIN games gm ON g.id = gm.genre_id AND gm.status = 'approved'
                GROUP BY g.id, g.name
                ORDER BY game_count DESC
            """)
            return [{'id': row[0], 'name': row[1], 'count': row[2]} for row in cursor.fetchall()]

    def get_authors(self):
        """Получает список авторов с одобренными играми"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT u.id, u.name 
                FROM users u
                INNER JOIN games g ON u.id = g.author_id
                WHERE g.status = 'approved'
                ORDER BY u.name
            """)
            return [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    def get_all_games(self):
        """Получает все игры (для администратора)"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT g.*, u.name as author_name,
                       COALESCE(AVG(r.rating), 0) as avg_rating,
                       COUNT(r.id) as review_count,
                       gn.name as genre_name
                FROM games g
                LEFT JOIN users u ON g.author_id = u.id
                LEFT JOIN reviews r ON g.id = r.game_id
                LEFT JOIN genres gn ON g.genre_id = gn.id
                GROUP BY g.id, u.name, gn.name
                ORDER BY g.created_at DESC
            """)
            return [dict(zip([column[0] for column in cursor.description], row)) 
                   for row in cursor.fetchall()]

    def get_author_games(self, author_id):
        """Получает игры автора"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT g.*, 
                       COALESCE(AVG(r.rating), 0) as avg_rating,
                       COUNT(r.id) as review_count,
                       gn.name as genre_name
                FROM games g
                LEFT JOIN reviews r ON g.id = r.game_id
                LEFT JOIN genres gn ON g.genre_id = gn.id
                WHERE g.author_id = %s
                GROUP BY g.id, gn.name
                ORDER BY g.created_at DESC
            """, (author_id,))
            return [dict(zip([column[0] for column in cursor.description], row)) 
                   for row in cursor.fetchall()]

    def get_purchased_games(self, buyer_id):
        """Получает купленные игры"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT g.*, 
                       COALESCE(AVG(r.rating), 0) as avg_rating,
                       COUNT(r.id) as review_count,
                       gn.name as genre_name,
                       o.created_at as purchase_date
                FROM games g
                JOIN order_items oi ON g.id = oi.game_id
                JOIN orders o ON oi.order_id = o.id
                LEFT JOIN reviews r ON g.id = r.game_id
                LEFT JOIN genres gn ON g.genre_id = gn.id
                WHERE o.buyer_id = %s AND o.status = 'paid'
                GROUP BY g.id, gn.name, o.created_at
                ORDER BY o.created_at DESC
            """, (buyer_id,))
            return [dict(zip([column[0] for column in cursor.description], row)) 
                   for row in cursor.fetchall()]

    def game_exists_by_title(self, title):
        """Проверяет, существует ли игра с таким названием"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM games WHERE LOWER(title) = LOWER(%s)', (title,))
            count = cursor.fetchone()[0]
            return count > 0 