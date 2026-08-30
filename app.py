import os
from datetime import date, datetime
from decimal import Decimal
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app=Flask(__name__)
app.secret_key=os.getenv('SECRET_KEY','dev-change-this')
db_url=os.getenv('DATABASE_URL','sqlite:///tea.db').replace('postgres://','postgresql://')
app.config.update(SQLALCHEMY_DATABASE_URI=db_url,SQLALCHEMY_TRACK_MODIFICATIONS=False)
db=SQLAlchemy(app)
BUSINESS=os.getenv('BUSINESS_NAME','GREEN STAR TEA ESTATE MANAGEMENT SYSTEM')
ROLES=['Administrator','Estate Manager','Factory Manager','Supervisor','Accountant','Store Manager','Driver']

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True); username=db.Column(db.String(80),unique=True,nullable=False); password=db.Column(db.String(255),nullable=False); role=db.Column(db.String(40),nullable=False); active=db.Column(db.Boolean,default=True); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Estate(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),unique=True,nullable=False); location=db.Column(db.String(160)); manager=db.Column(db.String(120)); status=db.Column(db.String(30),default='Active')
class Field(db.Model):
    id=db.Column(db.Integer,primary_key=True); estate_id=db.Column(db.Integer,db.ForeignKey('estate.id'),nullable=False); name=db.Column(db.String(100),nullable=False); acres=db.Column(db.Numeric(12,2),default=0); variety=db.Column(db.String(80)); planting_year=db.Column(db.Integer); status=db.Column(db.String(30),default='Active'); estate=db.relationship('Estate')
class Worker(db.Model):
    id=db.Column(db.Integer,primary_key=True); worker_no=db.Column(db.String(40),unique=True,nullable=False); name=db.Column(db.String(150),nullable=False); phone=db.Column(db.String(40)); id_no=db.Column(db.String(60)); department=db.Column(db.String(80),default='Plucking'); section=db.Column(db.String(100)); payment_method=db.Column(db.String(40),default='M-Pesa'); status=db.Column(db.String(30),default='Active')
class Rate(db.Model):
    id=db.Column(db.Integer,primary_key=True); rate=db.Column(db.Numeric(12,2),nullable=False); effective_from=db.Column(db.Date,nullable=False); effective_to=db.Column(db.Date); active=db.Column(db.Boolean,default=True)
class Plucking(db.Model):
    id=db.Column(db.Integer,primary_key=True); work_date=db.Column(db.Date,index=True,nullable=False); worker_id=db.Column(db.Integer,db.ForeignKey('worker.id'),nullable=False); field_id=db.Column(db.Integer,db.ForeignKey('field.id')); kg=db.Column(db.Numeric(12,2),nullable=False); rate=db.Column(db.Numeric(12,2),nullable=False); amount=db.Column(db.Numeric(14,2),nullable=False); status=db.Column(db.String(30),default='Pending',index=True); verified_by=db.Column(db.String(100)); worker=db.relationship('Worker'); field=db.relationship('Field')
class TeaIntake(db.Model):
    id=db.Column(db.Integer,primary_key=True); intake_date=db.Column(db.Date,nullable=False); estate_id=db.Column(db.Integer,db.ForeignKey('estate.id')); collection_kg=db.Column(db.Numeric(14,2),default=0); factory_kg=db.Column(db.Numeric(14,2),default=0); vehicle=db.Column(db.String(60)); driver=db.Column(db.String(120)); estate=db.relationship('Estate')
class Grade(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(80),unique=True,nullable=False); stock_kg=db.Column(db.Numeric(14,2),default=0); unit_price=db.Column(db.Numeric(14,2),default=0); active=db.Column(db.Boolean,default=True)
class Production(db.Model):
    id=db.Column(db.Integer,primary_key=True); production_date=db.Column(db.Date,nullable=False); grade_id=db.Column(db.Integer,db.ForeignKey('grade.id'),nullable=False); input_kg=db.Column(db.Numeric(14,2),default=0); output_kg=db.Column(db.Numeric(14,2),default=0); waste_kg=db.Column(db.Numeric(14,2),default=0); batch_no=db.Column(db.String(80)); grade=db.relationship('Grade')
class Supplier(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(150),unique=True,nullable=False); phone=db.Column(db.String(50)); email=db.Column(db.String(120))
class Item(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(150),unique=True,nullable=False); category=db.Column(db.String(80)); unit=db.Column(db.String(30),default='pcs'); quantity=db.Column(db.Numeric(14,2),default=0); min_stock=db.Column(db.Numeric(14,2),default=0); cost=db.Column(db.Numeric(14,2),default=0)
class StockTxn(db.Model):
    id=db.Column(db.Integer,primary_key=True); item_id=db.Column(db.Integer,db.ForeignKey('item.id'),nullable=False); txn_type=db.Column(db.String(40),nullable=False); quantity=db.Column(db.Numeric(14,2),nullable=False); unit_cost=db.Column(db.Numeric(14,2),default=0); reference=db.Column(db.String(100)); txn_date=db.Column(db.Date,default=date.today); item=db.relationship('Item')
class Vehicle(db.Model):
    id=db.Column(db.Integer,primary_key=True); reg_no=db.Column(db.String(40),unique=True,nullable=False); model=db.Column(db.String(80)); driver=db.Column(db.String(120)); status=db.Column(db.String(30),default='Active'); mileage=db.Column(db.Numeric(12,1),default=0)
class Trip(db.Model):
    id=db.Column(db.Integer,primary_key=True); trip_date=db.Column(db.Date,default=date.today); vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id')); driver=db.Column(db.String(120)); pickup=db.Column(db.String(150)); destination=db.Column(db.String(150)); kg=db.Column(db.Numeric(14,2)); reference=db.Column(db.String(100)); vehicle=db.relationship('Vehicle')
class Buyer(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(150),unique=True,nullable=False); phone=db.Column(db.String(50)); email=db.Column(db.String(120))
class TeaSale(db.Model):
    id=db.Column(db.Integer,primary_key=True); sale_date=db.Column(db.Date,default=date.today); buyer_id=db.Column(db.Integer,db.ForeignKey('buyer.id')); grade_id=db.Column(db.Integer,db.ForeignKey('grade.id')); quantity_kg=db.Column(db.Numeric(14,2)); price_per_kg=db.Column(db.Numeric(14,2)); total=db.Column(db.Numeric(16,2)); status=db.Column(db.String(30),default='Completed'); buyer=db.relationship('Buyer'); grade=db.relationship('Grade')
class Advance(db.Model):
    id=db.Column(db.Integer,primary_key=True); worker_id=db.Column(db.Integer,db.ForeignKey('worker.id')); amount=db.Column(db.Numeric(14,2)); advance_date=db.Column(db.Date,default=date.today); note=db.Column(db.String(255)); worker=db.relationship('Worker')
class Deduction(db.Model):
    id=db.Column(db.Integer,primary_key=True); worker_id=db.Column(db.Integer,db.ForeignKey('worker.id')); amount=db.Column(db.Numeric(14,2)); deduction_date=db.Column(db.Date,default=date.today); note=db.Column(db.String(255)); worker=db.relationship('Worker')
class Attendance(db.Model):
    id=db.Column(db.Integer,primary_key=True); worker_id=db.Column(db.Integer,db.ForeignKey('worker.id')); attend_date=db.Column(db.Date,nullable=False); status=db.Column(db.String(30)); worker=db.relationship('Worker')
class Payroll(db.Model):
    id=db.Column(db.Integer,primary_key=True); worker_id=db.Column(db.Integer,db.ForeignKey('worker.id')); month=db.Column(db.String(7),index=True); total_kg=db.Column(db.Numeric(14,2),default=0); gross=db.Column(db.Numeric(14,2),default=0); advances=db.Column(db.Numeric(14,2),default=0); deductions=db.Column(db.Numeric(14,2),default=0); net=db.Column(db.Numeric(14,2),default=0); status=db.Column(db.String(30),default='Draft'); payment_ref=db.Column(db.String(100)); paid_at=db.Column(db.DateTime); worker=db.relationship('Worker')
class Expense(db.Model):
    id=db.Column(db.Integer,primary_key=True); expense_date=db.Column(db.Date,default=date.today); category=db.Column(db.String(100)); description=db.Column(db.String(255)); amount=db.Column(db.Numeric(14,2)); status=db.Column(db.String(30),default='Pending'); approved_by=db.Column(db.String(100))
class Audit(db.Model):
    id=db.Column(db.Integer,primary_key=True); username=db.Column(db.String(80)); action=db.Column(db.String(255)); created_at=db.Column(db.DateTime,default=datetime.utcnow)

def me(): return User.query.get(session.get('uid')) if session.get('uid') else None
def guard(*roles):
    def deco(fn):
        @wraps(fn)
        def inner(*a,**kw):
            u=me()
            if not u: return redirect(url_for('login',next=request.path))
            if roles and u.role not in roles: return ('Forbidden',403)
            return fn(*a,**kw)
        return inner
    return deco
def audit(text):
    u=me(); db.session.add(Audit(username=u.username if u else 'system',action=text)); db.session.commit()
def D(x): return Decimal(str(x or 0))
def month_bounds(m):
    y,mo=map(int,m.split('-')); start=date(y,mo,1); end=date(y+1,1,1) if mo==12 else date(y,mo+1,1); return start,end
def current_rate(d):
    r=Rate.query.filter(Rate.active==True,Rate.effective_from<=d,db.or_(Rate.effective_to==None,Rate.effective_to>=d)).order_by(Rate.effective_from.desc()).first(); return D(r.rate) if r else Decimal('0')
@app.context_processor
def common(): return {'user':me(),'business':BUSINESS,'today':date.today(),'roles':ROLES}

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=User.query.filter_by(username=request.form.get('username','').strip()).first()
        if u and u.active and check_password_hash(u.password,request.form.get('password','')):
            session.clear(); session['uid']=u.id; return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid login details.','danger')
    return render_template('login.html')
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/')
@guard()
def dashboard():
    m=date.today().strftime('%Y-%m'); start,end=month_bounds(m)
    kg=sum((D(x.kg) for x in Plucking.query.filter(Plucking.work_date>=start,Plucking.work_date<end,Plucking.status=='Verified')),Decimal())
    payroll=sum((D(x.net) for x in Payroll.query.filter_by(month=m)),Decimal())
    sales=sum((D(x.total) for x in TeaSale.query.filter(TeaSale.sale_date>=start,TeaSale.sale_date<end,TeaSale.status=='Completed')),Decimal())
    expenses=sum((D(x.amount) for x in Expense.query.filter(Expense.expense_date>=start,Expense.expense_date<end,Expense.status=='Approved')),Decimal())
    intake=sum((D(x.factory_kg) for x in TeaIntake.query.filter(TeaIntake.intake_date>=start,TeaIntake.intake_date<end)),Decimal())
    return render_template('dashboard.html',kg=kg,payroll=payroll,sales=sales,expenses=expenses,intake=intake,profit=sales-expenses-payroll,workers=Worker.query.filter_by(status='Active').count(),fields=Field.query.filter_by(status='Active').count())

@app.route('/estates',methods=['GET','POST'])
@guard('Administrator','Estate Manager')
def estates():
    if request.method=='POST': db.session.add(Estate(name=request.form['name'],location=request.form.get('location'),manager=request.form.get('manager'))); db.session.commit(); audit('Added estate'); flash('Estate added.','success'); return redirect(url_for('estates'))
    return render_template('estates.html',rows=Estate.query.order_by(Estate.name).all())
@app.route('/fields',methods=['GET','POST'])
@guard('Administrator','Estate Manager')
def fields():
    if request.method=='POST': db.session.add(Field(estate_id=int(request.form['estate_id']),name=request.form['name'],acres=D(request.form.get('acres')),variety=request.form.get('variety'),planting_year=int(request.form['planting_year']) if request.form.get('planting_year') else None)); db.session.commit(); audit('Added field'); flash('Field added.','success'); return redirect(url_for('fields'))
    return render_template('fields.html',rows=Field.query.order_by(Field.name).all(),estates=Estate.query.all())
@app.route('/workers',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Supervisor')
def workers():
    if request.method=='POST': db.session.add(Worker(worker_no=request.form['worker_no'],name=request.form['name'],phone=request.form.get('phone'),id_no=request.form.get('id_no'),department=request.form.get('department') or 'Plucking',section=request.form.get('section'),payment_method=request.form.get('payment_method') or 'M-Pesa')); db.session.commit(); audit('Added worker'); flash('Worker added.','success'); return redirect(url_for('workers'))
    return render_template('workers.html',rows=Worker.query.order_by(Worker.name).all())
@app.route('/rates',methods=['GET','POST'])
@guard('Administrator','Estate Manager')
def rates():
    if request.method=='POST': db.session.add(Rate(rate=D(request.form['rate']),effective_from=datetime.strptime(request.form['from'],'%Y-%m-%d').date())); db.session.commit(); audit('Added tea rate'); flash('Rate saved.','success'); return redirect(url_for('rates'))
    return render_template('rates.html',rows=Rate.query.order_by(Rate.effective_from.desc()).all())
@app.route('/plucking',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Supervisor')
def plucking():
    if request.method=='POST':
        d=datetime.strptime(request.form['date'],'%Y-%m-%d').date(); rate=current_rate(d)
        if rate<=0: flash('Set a tea rate first.','danger'); return redirect(url_for('rates'))
        kg=D(request.form['kg']); x=Plucking(work_date=d,worker_id=int(request.form['worker_id']),field_id=int(request.form['field_id']) if request.form.get('field_id') else None,kg=kg,rate=rate,amount=kg*rate); db.session.add(x); db.session.commit(); audit('Recorded plucking'); flash('Plucking recorded for verification.','success'); return redirect(url_for('plucking'))
    return render_template('plucking.html',rows=Plucking.query.order_by(Plucking.work_date.desc(),Plucking.id.desc()).limit(500).all(),workers=Worker.query.filter_by(status='Active').all(),fields=Field.query.filter_by(status='Active').all())
@app.route('/plucking/<int:i>/verify')
@guard('Administrator','Estate Manager','Supervisor')
def verify_plucking(i):
    x=Plucking.query.get_or_404(i); x.status='Verified'; x.verified_by=me().username; db.session.commit(); audit('Verified plucking'); flash('Verified.','success'); return redirect(url_for('plucking'))

@app.route('/intake',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Factory Manager','Supervisor')
def intake():
    if request.method=='POST': db.session.add(TeaIntake(intake_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),estate_id=int(request.form['estate_id']),collection_kg=D(request.form['collection_kg']),factory_kg=D(request.form['factory_kg']),vehicle=request.form.get('vehicle'),driver=request.form.get('driver'))); db.session.commit(); audit('Recorded tea intake'); flash('Factory intake recorded.','success'); return redirect(url_for('intake'))
    return render_template('intake.html',rows=TeaIntake.query.order_by(TeaIntake.intake_date.desc()).all(),estates=Estate.query.all())
@app.route('/production',methods=['GET','POST'])
@guard('Administrator','Factory Manager')
def production():
    if request.method=='POST':
        g=Grade.query.get(int(request.form['grade_id'])); out=D(request.form['output_kg']); g.stock_kg=D(g.stock_kg)+out
        db.session.add(Production(production_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),grade_id=g.id,input_kg=D(request.form['input_kg']),output_kg=out,waste_kg=D(request.form.get('waste_kg')),batch_no=request.form.get('batch_no'))); db.session.commit(); audit('Recorded factory production'); flash('Production recorded.','success'); return redirect(url_for('production'))
    return render_template('production.html',rows=Production.query.order_by(Production.production_date.desc()).all(),grades=Grade.query.all())
@app.route('/grades',methods=['GET','POST'])
@guard('Administrator','Factory Manager')
def grades():
    if request.method=='POST': db.session.add(Grade(name=request.form['name'],unit_price=D(request.form.get('price')))); db.session.commit(); audit('Added tea grade'); flash('Grade added.','success'); return redirect(url_for('grades'))
    return render_template('grades.html',rows=Grade.query.all())

@app.route('/inventory',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Store Manager')
def inventory():
    if request.method=='POST':
        item=Item(name=request.form['name'],category=request.form.get('category'),unit=request.form.get('unit') or 'pcs',min_stock=D(request.form.get('min_stock')),cost=D(request.form.get('cost'))); qty=D(request.form.get('opening')); item.quantity=qty; db.session.add(item); db.session.flush()
        if qty: db.session.add(StockTxn(item_id=item.id,txn_type='Opening',quantity=qty,unit_cost=item.cost,reference='OPENING'))
        db.session.commit(); audit('Added inventory item'); flash('Item added.','success'); return redirect(url_for('inventory'))
    return render_template('inventory.html',rows=Item.query.order_by(Item.name).all())
@app.route('/inventory/<int:i>/transaction',methods=['POST'])
@guard('Administrator','Estate Manager','Store Manager')
def inventory_txn(i):
    item=Item.query.get_or_404(i); qty=D(request.form['quantity']); typ=request.form['type']; signed=qty if typ in ('Purchase','Return') else -qty
    item.quantity=D(item.quantity)+signed; db.session.add(StockTxn(item_id=i,txn_type=typ,quantity=signed,unit_cost=D(request.form.get('cost') or item.cost),reference=request.form.get('reference'))); db.session.commit(); audit('Updated stock '+item.name); flash('Stock updated.','success'); return redirect(url_for('inventory'))

@app.route('/buyers',methods=['GET','POST'])
@guard('Administrator','Accountant','Estate Manager')
def buyers():
    if request.method=='POST': db.session.add(Buyer(name=request.form['name'],phone=request.form.get('phone'),email=request.form.get('email'))); db.session.commit(); audit('Added tea buyer'); flash('Buyer added.','success'); return redirect(url_for('buyers'))
    return render_template('buyers.html',rows=Buyer.query.all())
@app.route('/sales',methods=['GET','POST'])
@guard('Administrator','Accountant','Estate Manager')
def sales():
    if request.method=='POST':
        g=Grade.query.get(int(request.form['grade_id'])); qty=D(request.form['quantity']); price=D(request.form['price']);
        if D(g.stock_kg)<qty: flash('Insufficient finished tea stock.','danger'); return redirect(url_for('sales'))
        g.stock_kg=D(g.stock_kg)-qty; db.session.add(TeaSale(sale_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),buyer_id=int(request.form['buyer_id']),grade_id=g.id,quantity_kg=qty,price_per_kg=price,total=qty*price)); db.session.commit(); audit('Recorded tea sale'); flash('Tea sale recorded.','success'); return redirect(url_for('sales'))
    return render_template('sales.html',rows=TeaSale.query.order_by(TeaSale.sale_date.desc()).all(),buyers=Buyer.query.all(),grades=Grade.query.all())

@app.route('/attendance',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Supervisor')
def attendance():
    if request.method=='POST': db.session.add(Attendance(worker_id=int(request.form['worker_id']),attend_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),status=request.form['status'])); db.session.commit(); audit('Recorded attendance'); flash('Attendance saved.','success'); return redirect(url_for('attendance'))
    return render_template('attendance.html',rows=Attendance.query.order_by(Attendance.attend_date.desc()).limit(500).all(),workers=Worker.query.filter_by(status='Active').all())
@app.route('/advances',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Accountant')
def advances():
    if request.method=='POST': db.session.add(Advance(worker_id=int(request.form['worker_id']),amount=D(request.form['amount']),advance_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),note=request.form.get('note'))); db.session.commit(); audit('Recorded worker advance'); flash('Advance recorded.','success'); return redirect(url_for('advances'))
    return render_template('advances.html',rows=Advance.query.order_by(Advance.advance_date.desc()).all(),workers=Worker.query.filter_by(status='Active').all())
@app.route('/deductions',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Accountant')
def deductions():
    if request.method=='POST': db.session.add(Deduction(worker_id=int(request.form['worker_id']),amount=D(request.form['amount']),deduction_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),note=request.form.get('note'))); db.session.commit(); audit('Recorded deduction'); flash('Deduction recorded.','success'); return redirect(url_for('deductions'))
    return render_template('deductions.html',rows=Deduction.query.order_by(Deduction.deduction_date.desc()).all(),workers=Worker.query.filter_by(status='Active').all())
@app.route('/payroll',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Accountant')
def payroll():
    month=request.args.get('month',date.today().strftime('%Y-%m'))
    if request.method=='POST':
        month=request.form['month']; start,end=month_bounds(month)
        for w in Worker.query.filter_by(status='Active').all():
            rows=Plucking.query.filter_by(worker_id=w.id,status='Verified').filter(Plucking.work_date>=start,Plucking.work_date<end).all(); gross=sum((D(x.amount) for x in rows),Decimal()); kg=sum((D(x.kg) for x in rows),Decimal()); adv=sum((D(x.amount) for x in Advance.query.filter_by(worker_id=w.id).filter(Advance.advance_date>=start,Advance.advance_date<end).all()),Decimal()); ded=sum((D(x.amount) for x in Deduction.query.filter_by(worker_id=w.id).filter(Deduction.deduction_date>=start,Deduction.deduction_date<end).all()),Decimal()); x=Payroll.query.filter_by(worker_id=w.id,month=month).first() or Payroll(worker_id=w.id,month=month); x.total_kg=kg;x.gross=gross;x.advances=adv;x.deductions=ded;x.net=gross-adv-ded;x.status='Draft';db.session.add(x)
        db.session.commit(); audit('Generated payroll '+month); flash('Payroll generated.','success'); return redirect(url_for('payroll',month=month))
    return render_template('payroll.html',month=month,rows=Payroll.query.filter_by(month=month).order_by(Payroll.net.desc()).all())
@app.route('/payroll/<int:i>/approve')
@guard('Administrator','Estate Manager','Accountant')
def approve_payroll(i):
    x=Payroll.query.get_or_404(i); x.status='Approved'; db.session.commit(); audit('Approved payroll'); flash('Payroll approved.','success'); return redirect(url_for('payroll',month=x.month))
@app.route('/payroll/<int:i>/pay',methods=['POST'])
@guard('Administrator','Estate Manager','Accountant')
def pay_payroll(i):
    x=Payroll.query.get_or_404(i)
    if x.status!='Approved': flash('Approve payroll first.','danger'); return redirect(url_for('payroll',month=x.month))
    x.status='Paid'; x.paid_at=datetime.utcnow(); x.payment_ref=request.form.get('reference'); db.session.commit(); audit('Paid payroll'); flash('Payroll marked paid.','success'); return redirect(url_for('payroll',month=x.month))

@app.route('/expenses',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Accountant')
def expenses():
    if request.method=='POST': db.session.add(Expense(expense_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),category=request.form['category'],description=request.form.get('description'),amount=D(request.form['amount']))); db.session.commit(); audit('Recorded expense'); flash('Expense submitted.','success'); return redirect(url_for('expenses'))
    return render_template('expenses.html',rows=Expense.query.order_by(Expense.expense_date.desc()).all())
@app.route('/expenses/<int:i>/approve')
@guard('Administrator','Estate Manager','Accountant')
def approve_expense(i):
    x=Expense.query.get_or_404(i); x.status='Approved'; x.approved_by=me().username; db.session.commit(); audit('Approved expense'); flash('Expense approved.','success'); return redirect(url_for('expenses'))
@app.route('/vehicles',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Driver')
def vehicles():
    if request.method=='POST': db.session.add(Vehicle(reg_no=request.form['reg_no'],model=request.form.get('model'),driver=request.form.get('driver'))); db.session.commit(); audit('Added vehicle'); flash('Vehicle added.','success'); return redirect(url_for('vehicles'))
    return render_template('vehicles.html',rows=Vehicle.query.all())
@app.route('/trips',methods=['GET','POST'])
@guard('Administrator','Estate Manager','Driver')
def trips():
    if request.method=='POST': db.session.add(Trip(trip_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),vehicle_id=int(request.form['vehicle_id']),driver=request.form['driver'],pickup=request.form['pickup'],destination=request.form['destination'],kg=D(request.form['kg']),reference=request.form.get('reference'))); db.session.commit(); audit('Recorded transport trip'); flash('Trip recorded.','success'); return redirect(url_for('trips'))
    return render_template('trips.html',rows=Trip.query.order_by(Trip.trip_date.desc()).all(),vehicles=Vehicle.query.all())

@app.route('/reports')
@guard('Administrator','Estate Manager','Accountant','Factory Manager')
def reports():
    m=request.args.get('month',date.today().strftime('%Y-%m')); start,end=month_bounds(m); p=Plucking.query.filter(Plucking.work_date>=start,Plucking.work_date<end,Plucking.status=='Verified').all(); s=TeaSale.query.filter(TeaSale.sale_date>=start,TeaSale.sale_date<end,TeaSale.status=='Completed').all(); e=Expense.query.filter(Expense.expense_date>=start,Expense.expense_date<end,Expense.status=='Approved').all(); kg=sum((D(x.kg) for x in p),Decimal()); tea_pay=sum((D(x.amount) for x in p),Decimal()); revenue=sum((D(x.total) for x in s),Decimal()); exp=sum((D(x.amount) for x in e),Decimal()); by_worker={}
    for x in p: by_worker[x.worker.name]=by_worker.get(x.worker.name,Decimal())+D(x.kg)
    return render_template('reports.html',month=m,kg=kg,tea_pay=tea_pay,revenue=revenue,expenses=exp,profit=revenue-exp,by_worker=sorted(by_worker.items(),key=lambda z:z[1],reverse=True))
@app.route('/users',methods=['GET','POST'])
@guard('Administrator')
def users():
    if request.method=='POST':
        if User.query.filter_by(username=request.form['username']).first(): flash('Username exists.','danger'); return redirect(url_for('users'))
        u=User(username=request.form['username'],password=generate_password_hash(request.form['password']),role=request.form['role']); db.session.add(u); db.session.commit(); audit('Created user '+u.username); flash('User created.','success'); return redirect(url_for('users'))
    return render_template('users.html',rows=User.query.order_by(User.username).all())
@app.route('/audit')
@guard('Administrator','Estate Manager')
def audit_page(): return render_template('audit.html',rows=Audit.query.order_by(Audit.created_at.desc()).limit(1000).all())
@app.route('/health')
def health(): return jsonify(status='ok',application=BUSINESS)

@app.cli.command('init-db')
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin',password=generate_password_hash(os.getenv('ADMIN_PASSWORD','Admin@12345')),role='Administrator'))
    if not Grade.query.first():
        for n in ['BP1','PF1','PD','Dust','Fannings']: db.session.add(Grade(name=n))
    if not Estate.query.first(): db.session.add(Estate(name='Main Estate',location='Kenya',manager=''))
    db.session.commit(); print('Database initialized.')

if __name__=='__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')))
