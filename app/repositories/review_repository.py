class ReviewRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def _row_to_dict(self, row, description):
        if row is None:
            return None
        return {desc[0]: value for desc, value in zip(description, row)}

    def get_game_reviews(self, game_id):
        """Получает отзывы для конкретной игры"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT r.*, u.name as user_name, u.role as user_role
                FROM reviews r
                JOIN users u ON r.user_id = u.id
                WHERE r.game_id = %s
                ORDER BY r.created_at DESC
            """, (game_id,))
            reviews = cursor.fetchall()
            return [self._row_to_dict(review, cursor.description) for review in reviews]

    def get_game_rating(self, game_id):
        """Получает средний рейтинг и количество отзывов для игры"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COALESCE(AVG(rating), 0) as avg_rating,
                    COUNT(*) as review_count
                FROM reviews
                WHERE game_id = %s
            """, (game_id,))
            result = cursor.fetchone()
            cursor.fetchall()
            return {
                'avg_rating': float(result[0]),
                'review_count': result[1]
            }

    def create_review(self, user_id, game_id, rating, comment):
        """Создает новый отзыв"""
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO reviews (user_id, game_id, rating, comment)
                VALUES (%s, %s, %s, %s)
            """, (user_id, game_id, rating, comment))
            connection.commit()

    def has_user_reviewed(self, user_id, game_id):
        """Проверяет, оставил ли пользователь отзыв на игру"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM reviews 
                WHERE user_id = %s AND game_id = %s
            """, (user_id, game_id))
            result = cursor.fetchone()
            cursor.fetchall()
            return result is not None 