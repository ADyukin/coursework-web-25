class CartRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_cart_items(self, cart_items):
        """Получает информацию об играх в корзине"""
        if not cart_items:
            return [], 0

        with self.db_connector.connect().cursor() as cursor:
            placeholders = ','.join(['%s'] * len(cart_items))
            cursor.execute(f'''
                SELECT g.*, u.name as author_name, 
                       COALESCE(AVG(r.rating), 0) as avg_rating,
                       COUNT(r.id) as review_count
                FROM games g
                LEFT JOIN users u ON g.author_id = u.id
                LEFT JOIN reviews r ON g.id = r.game_id
                WHERE g.id IN ({placeholders})
                GROUP BY g.id
            ''', cart_items)
            
            results = cursor.fetchall()
            items = []
            total = 0
            
            for row in results:
                item = {desc[0]: value for desc, value in zip(cursor.description, row)}
                items.append(item)
                total += item['price']
            
            return items, total

    def create_order(self, buyer_id, total_amount, cart_items):
        """Создает заказ из корзины"""
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            # Создаем заказ
            cursor.execute('''
                INSERT INTO orders (buyer_id, total_amount, status)
                VALUES (%s, %s, 'paid')
            ''', (buyer_id, total_amount))
            
            # Получаем ID созданного заказа
            order_id = cursor.lastrowid
            
            # Добавляем игры в заказ
            for game_id in cart_items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, game_id, price)
                    SELECT %s, id, price
                    FROM games
                    WHERE id = %s
                ''', (order_id, game_id))
            
            connection.commit()
            return order_id 