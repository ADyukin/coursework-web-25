class OrderRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def _row_to_dict(self, row, description):
        if row is None:
            return None
        return {desc[0]: value for desc, value in zip(description, row)}

    def get_user_orders(self, user_id):
        """Получает список заказов пользователя"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute('''
                SELECT o.*, 
                       GROUP_CONCAT(g.id SEPARATOR ',') as game_ids,
                       GROUP_CONCAT(g.title SEPARATOR ',') as game_titles,
                       GROUP_CONCAT(g.image_url SEPARATOR ',') as game_images,
                       GROUP_CONCAT(oi.price SEPARATOR ',') as game_prices
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                LEFT JOIN games g ON oi.game_id = g.id
                WHERE o.buyer_id = %s
                GROUP BY o.id
                ORDER BY o.created_at DESC
            ''', (user_id,))
            
            orders = []
            for row in cursor.fetchall():
                order = self._row_to_dict(row, cursor.description)
                
                # Преобразуем строки с данными игр в списки
                game_ids = order['game_ids'].split(',') if order['game_ids'] else []
                game_titles = order['game_titles'].split(',') if order['game_titles'] else []
                game_images = order['game_images'].split(',') if order['game_images'] else []
                game_prices = order['game_prices'].split(',') if order['game_prices'] else []
                
                # Создаем список предметов заказа
                order['order_items'] = []
                for i in range(len(game_ids)):
                    order['order_items'].append({
                        'game': {
                            'id': game_ids[i],
                            'title': game_titles[i],
                            'image_url': game_images[i]
                        },
                        'price': float(game_prices[i])
                    })
                
                # Удаляем ненужные поля
                del order['game_ids']
                del order['game_titles']
                del order['game_images']
                del order['game_prices']
                
                orders.append(order)
            
            return orders

    def get_order_by_id(self, order_id):
        """Получает информацию о конкретном заказе"""
        with self.db_connector.connect().cursor() as cursor:
            cursor.execute('''
                SELECT o.*, 
                       GROUP_CONCAT(g.id SEPARATOR ',') as game_ids,
                       GROUP_CONCAT(g.title SEPARATOR ',') as game_titles,
                       GROUP_CONCAT(g.image_url SEPARATOR ',') as game_images,
                       GROUP_CONCAT(oi.price SEPARATOR ',') as game_prices
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                LEFT JOIN games g ON oi.game_id = g.id
                WHERE o.id = %s
                GROUP BY o.id
            ''', (order_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            order = self._row_to_dict(row, cursor.description)
            
            # Преобразуем строки с данными игр в списки
            game_ids = order['game_ids'].split(',') if order['game_ids'] else []
            game_titles = order['game_titles'].split(',') if order['game_titles'] else []
            game_images = order['game_images'].split(',') if order['game_images'] else []
            game_prices = order['game_prices'].split(',') if order['game_prices'] else []
            
            # Создаем список предметов заказа
            order['order_items'] = []
            for i in range(len(game_ids)):
                order['order_items'].append({
                    'game': {
                        'id': game_ids[i],
                        'title': game_titles[i],
                        'image_url': game_images[i]
                    },
                    'price': float(game_prices[i])
                })
            
            # Удаляем ненужные поля
            del order['game_ids']
            del order['game_titles']
            del order['game_images']
            del order['game_prices']
            
            return order

    def update_order_status(self, order_id, status):
        """Обновляет статус заказа"""
        connection = self.db_connector.connect()
        with connection.cursor() as cursor:
            cursor.execute('''
                UPDATE orders 
                SET status = %s
                WHERE id = %s
            ''', (status, order_id))
            connection.commit()
            return cursor.rowcount > 0 