from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)


class NotEnoughDataException(Exception):
  pass


class NotEnoughMoneyException(Exception):
  pass


class NotEnoughStockException(Exception):
  pass


class NoActionException(Exception):
  pass

#region DB_Models
class Balance(db.Model):
  __tablename__ = 'Balance'
  id = db.Column(db.Integer, primary_key=True)
  bal = db.Column(db.Integer, nullable=False)

class Balance_change(db.Model):
  __tablename__ = 'Balance_change'
  id = db.Column(db.Integer, primary_key=True)
  change = db.Column(db.Integer, nullable=False)
  comment = db.Column(db.String(120), nullable=False)
  balance_history = db.relationship("History")

class Product_change(db.Model):
  __tablename__ = 'Product_change'
  id = db.Column(db.Integer, primary_key=True)
  op_type = db.Column(db.String(10), nullable=False)
  product_name = db.Column(db.String(60), nullable=False)
  single_price = db.Column(db.Integer, nullable=False)
  product_count = db.Column(db.Integer, nullable=False)
  product_history = db.relationship("History")

class Stock(db.Model):
  __tablename__ = 'Stock'
  id = db.Column(db.Integer, primary_key=True)
  product_name = db.Column(db.String(60), nullable=False, unique=True)
  product_stock = db.Column(db.Integer, nullable=False)

class History(db.Model):
  __tablename__ = 'History'
  id = db.Column(db.Integer, primary_key=True)
  balance_history = db.Column(db.Integer, db.ForeignKey('Balance_change.id'), nullable=True)
  product_history = db.Column(db.Integer, db.ForeignKey('Product_change.id'), nullable=True)
  last_id = db.Column(db.Integer, nullable=False)
#endregion

#region Manager
class Manager:
  def __init__(self, db):
    self.db = db
    self.actions = {}

#region DB_Functions
  def get_last_history_id(self):
    res = self.db.session.query(History).order_by(History.last_id.desc()).first()
    
    if res is None: # przypadku pustej historii zwraca 1
      return 0
    return res.last_id

  def get_user_balance_obj(self):
    return self.db.session.query(Balance).filter(Balance.id == 1).first()

  def edit_user_balance(self, value):
    res = self.get_user_balance_obj()
    res.bal += value
    self.db.session.add(res)
    self.db.session.commit()

  def enough_balance_to_change(self, value):
    bal = self.get_user_balance_obj().bal
    if value < 0: # odejmowanie z konta
      return bal + value >= 0 # bal + -x
    else: # dodawanie
      return True

  def enough_balance_to_buy(self, value):
    bal = self.get_user_balance_obj().bal
    if bal < value:
      return False
    else:
      return True

  def get_stock_by_name(self, name):
    res = self.db.session.query(Stock).filter(Stock.product_name == name).first()
    if res is None:
      raise NotEnoughStockException()
    return res.product_stock

  def get_whole_stock(self):
    res = self.db.session.query(Stock).all()
    stock_arr = {}
    for stock in res:
      stock_arr[stock.product_name] = stock.product_stock
    return stock_arr

  def is_in_stock(self, name, count):
    return self.get_stock_by_name(name) >= count

  def add_to_stock(self, name, count):
    res = self.db.session.query(Stock).filter(Stock.product_name == name).first()
    if res:
      res.product_stock+= count
      self.db.session.add(res)
      self.db.session.commit()
    else:
      obj = Stock(product_name=name, product_stock=count)
      self.db.session.add(obj)
      self.db.session.commit()

  def remove_from_stock(self, name, count):
    if self.is_in_stock(name, count):
      obj = self.db.session.query(Stock).filter(Stock.product_name == name).first()
      obj.product_stock -= count
      self.db.session.add(obj)
      self.db.session.commit()
    else:
      raise NotEnoughStockException()

  def insert_to_history(self, type, id): #type 0 = bal 1 = prod
    last_id = self.get_last_history_id()+1
    if type == 0:
      obj = History(balance_history=id, product_history=None, last_id=last_id)
    elif type == 1:
      obj = History(balance_history=None, product_history=id, last_id=last_id)
    self.db.session.add(obj)
    self.db.session.commit()

  def change_balance(self, change, comment):
    obj_balance_change = Balance_change(change=change, comment=comment)
    self.db.session.add(obj_balance_change)
    self.db.session.commit()
    self.edit_user_balance(change)
    self.insert_to_history(0, obj_balance_change.id)

  def product_operation(self, op_type, product_name, single_price, product_count): #op_type = zakup/sprzedaz
    obj_product_operation = Product_change(op_type=op_type, product_name=product_name, single_price=single_price, product_count=product_count)
    
    if op_type == 'zakup': # -
      if self.enough_balance_to_buy(single_price*product_count):
        self.db.session.add(obj_product_operation)
        self.db.session.commit()
        self.add_to_stock(product_name, product_count)
        self.edit_user_balance(-(single_price*product_count))
        self.insert_to_history(1, obj_product_operation.id)
      else:
        raise NotEnoughMoneyException()
    elif op_type == 'sprzedaz': # +
      if self.is_in_stock(product_name, product_count):
        self.db.session.add(obj_product_operation)
        self.db.session.commit()
        self.remove_from_stock(product_name, product_count)
        self.edit_user_balance(single_price*product_count)
        self.insert_to_history(1, obj_product_operation.id)
      else:
        raise NotEnoughStockException()

  def get_history(self, start, end):
    #res_balance = self.db.session.query(Balance_change).join(History, History.balance_history == Balance_change.id, isinner=True).all()
    #res_product = self.db.session.query(Product_change).join(History, History.product_history == Product_change.id, isouter=True).all()
    # history_arr = []
    # for item in res_balance:
    #   history_arr.append('saldo', item.change, item.comment, None, )
    q = self.db.session.query(History, Balance_change
    ).filter(History.balance_history == Balance_change.id).all()
    q2 = self.db.session.query(History, Product_change
    ).filter(History.product_history == Product_change.id).all()

    formetted_arr = []

    for each in q:
      formetted_arr.append(('saldo', each[1].change, each[1].comment, None, each[0].last_id))
      #print(f'{each[0].last_id}:{each[1].comment}')
    for each in q2:
      formetted_arr.append((each[1].op_type, each[1].product_name, each[1].single_price, each[1].product_count, each[0].last_id))
      #print(f'{each[0].last_id}:{each[1].comment}')

    formetted_arr = sorted(formetted_arr, key=lambda x: x[-1])
    
    if start == '' and end == '':
      return formetted_arr
    else:
      array_in_range = []
      for each in formetted_arr:
        if each[4] >= int(start) and each[4] <= int(end):
          array_in_range.append(each)
      return array_in_range
#endregion

  def modify_balance(self, value, comment):
    if self.enough_balance_to_change(value):
      self.change_balance(value, comment)
    else:
      raise NotEnoughMoneyException()

  def add_history(self, row):
    self.history.append(row)

  def buy_item(self, name, price, qty):
    self.product_operation('zakup', name, price, qty)

  def sell_item(self, name, price, qty):
    self.product_operation('sprzedaz', name, price, qty)

  def action(self, name, parameters):
    def action_in(callback):
      self.actions[name] = (parameters, callback)
    return action_in

  def process_action(self, action, rows):
    parameters, callback = self.actions[action]
    if len(rows) != parameters:
      raise NoActionException()
    if callback(self, rows):
      print
#endregion

#region Accountant
manager = Manager(db)

@manager.action("saldo", 2)
def saldo(manager, rows):
  value = float(rows[0])
  comment = rows[1]
  manager.modify_balance(value, comment)
  return True

@manager.action("zakup", 3)
def zakup(manager, rows):
  name = rows[0]
  price = float(rows[1])
  qty = float(rows[2])
  manager.buy_item(name, price, qty)
  return True

@manager.action("sprzedaz", 3)
def sprzedaz(manager, rows):
  name = rows[0]
  price = float(rows[1])
  qty = float(rows[2])
  manager.sell_item(name, price, qty)
  return True

@manager.action("przeglad", 2)
def przeglad(manager, rows):
  #for row in manager.review(rows[0], rows[1]):
    #print(row)
  return True

@manager.action("magazyn", 0)
def magazyn(manager, rows):
  for item in rows:
    if item not in manager.stock:
      manager.stock[item] = 0.0
  #print(manager.stock)
#endregion

#region Routes
@app.route("/")
def index():
  manager.process_action("magazyn", [])
  return render_template('index.html', stock=manager.get_whole_stock())

@app.route("/buy")
def buy():
  return render_template('buy.html')

@app.route("/api/buy_product", methods=['POST']) # {'name': 'asd', 'price_one': '1', 'count': '22'}
def api_buy_product():
  request_json = request.get_json()
  try:
    manager.process_action("zakup", [request_json['name'], request_json['price_one'], request_json['count']])

  except NotEnoughMoneyException:
    return jsonify({'status': 'NotEnoughMoney'})

  else:
    return jsonify({'status': 'ok', 'newBalance': manager.get_user_balance_obj().bal})

@app.route("/sell")
def sell():
  return render_template('sell.html')

@app.route("/api/sell_product", methods=['POST']) # {'name': 'asd', 'price_one': '1', 'count': '22'}
def api_sell_product(): #NotEnoughStockException
  request_json = request.get_json()
  try:
    manager.process_action("sprzedaz", [request_json['name'], request_json['price_one'], request_json['count']])
    
  except NotEnoughStockException:
    return jsonify({'status': 'NotEnoughStock'})

  else:
    return jsonify({'status': 'ok', 'newBalance': manager.get_user_balance_obj().bal})

@app.route("/history")
def history():
  return render_template('history.html', history=manager.get_history('', ''))

@app.route("/history/<line_from>/<line_to>")
def history_bounds(line_from, line_to):
  return render_template('history.html', history=manager.get_history(line_from, line_to))

@app.route("/change_balance")
def change_balance():
  return render_template('change_balance.html')

@app.route("/api/change_balance", methods=['POST'])
def api_change_balance():
  request_json = request.get_json()
  try:
    manager.process_action("saldo", [request_json['value'], request_json['comment']])
    
  except NotEnoughMoneyException:
    return jsonify({'status': 'NotEnoughMoney'})

  else:
    return jsonify({'status': 'ok', 'newBalance': manager.get_user_balance_obj().bal})

@app.route("/api/get_bal", methods=['GET'])
def get_bal():
  return jsonify({'newBalance': manager.get_user_balance_obj().bal})
#endregion