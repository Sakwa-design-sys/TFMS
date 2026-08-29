import os
from datetime import date, datetime
from decimal import Decimal
from flask import Flask, request, redirect, url_for, render_template, session, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app=Flask(__name__)
app.secret_key=os.getenv('SECRET_KEY','change-this-secret')
db_url=os.getenv('DATABASE_URL','sqlite:///kapkosgei.db').replace('postgres://','postgresql://')
app.config['SQLALCHEMY_DATABASE_URI']=db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True); username=db.Column(db.String(80),unique=True,nullable=False); password=db.Column(db.String(255),nullable=False); role=db.Column(db.String(30),nullable=False); active=db.Column(db.Boolean,default=True)
class Worker(db.Model):
    id=db.Column(db.Integer,primary_key=True); worker_no=db.Column(db.String(40),unique=True,nullable=False); name=db.Column(db.String(150),nullable=False); phone=db.Column(db.String(40)); id_no=db.Column(db.String(60)); gender=db.Column(db.String(20)); section=db.Column(db.String(100)); supervisor=db.Column(db.String(150)); payment_method=db.Column(db.String(40)); status=db.Column(db.String(30),default='Active'); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Rate(db.Model):
    id=db.Column(db.Integer,primary_key=True); rate=db.Column(db.Numeric(12,2),nullable=False); effective_from=db.Column(db.Date,nullable=False); effective_to=db.Column(db.Date); active=db.Column(db.Boolean,default=True)
class Plucking(db.Model):
    id=db.Column(db.Integer,primary_key=True); work_date=db.Column(db.Date,nullable=False); worker_id=db.Column(db.Integer,db.ForeignKey('worker.id'),nullable=False); section=db.Column(db.String(100)); kg=db.Column(db.Numeric(12,2),nullable=False); rate=db.Column(db.Numeric(12,2),nullable=False); amount=db.Column(db.Numeric(14,2),nullable=False); status=db.Column(db.String(30),default='Pending'); verified_by=db.Column(db.String(100)); created_at=db.Column(db.DateTime,default=datetime.utcnow); worker=db.relationship('Worker')
class Advance(db.Model):
    id=db.Column(db.Integer,primary_key=True); worker_id=db.Column(db.Integer,db.ForeignKey('worker.id'),nullable=False); amount=db.Column(db.Numeric(14,2),nullable=False); advance_date=db.Column(db.Date,default=date.today); note=db.Column(db.String(255)); status=db.Column(db.String(30),default='Approved'); worker=db.relationship('Worker')
class Deduction(db.Model):
    id=db.Column(db.Integer,primary_key=True); worker_id=db.Column(db.Integer,db.ForeignKey('worker.id'),nullable=False); amount=db.Column(db.Numeric(14,2),nullable=False); deduction_date=db.Column(db.Date,default=date.today); note=db.Column(db.String(255)); worker=db.relationship('Worker')
class Payroll(db.Model):
    id=db.Column(db.Integer,primary_key=True); worker_id=db.Column(db.Integer,db.ForeignKey('worker.id'),nullable=False); month=db.Column(db.String(7),nullable=False); total_kg=db.Column(db.Numeric(14,2),default=0); gross=db.Column(db.Numeric(14,2),default=0); advances=db.Column(db.Numeric(14,2),default=0); deductions=db.Column(db.Numeric(14,2),default=0); net=db.Column(db.Numeric(14,2),default=0); status=db.Column(db.String(30),default='Draft'); paid_at=db.Column(db.DateTime); payment_ref=db.Column(db.String(100)); worker=db.relationship('Worker')
class Attendance(db.Model):
    id=db.Column(db.Integer,primary_key=True); worker_id=db.Column(db.Integer,db.ForeignKey('worker.id'),nullable=False); attend_date=db.Column(db.Date,nullable=False); status=db.Column(db.String(30),nullable=False); worker=db.relationship('Worker')
class Vehicle(db.Model):
    id=db.Column(db.Integer,primary_key=True); reg_no=db.Column(db.String(40),unique=True,nullable=False); model=db.Column(db.String(80)); driver=db.Column(db.String(150)); status=db.Column(db.String(30),default='Active'); mileage=db.Column(db.Numeric(12,1),default=0)
class Trip(db.Model):
    id=db.Column(db.Integer,primary_key=True); trip_date=db.Column(db.Date,default=date.today); vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id')); driver=db.Column(db.String(150)); pickup=db.Column(db.String(150)); destination=db.Column(db.String(150)); kg=db.Column(db.Numeric(12,2)); reference=db.Column(db.String(100)); vehicle=db.relationship('Vehicle')
class Expense(db.Model):
    id=db.Column(db.Integer,primary_key=True); expense_date=db.Column(db.Date,default=date.today); category=db.Column(db.String(100)); description=db.Column(db.String(255)); amount=db.Column(db.Numeric(14,2)); status=db.Column(db.String(30),default='Pending'); approved_by=db.Column(db.String(100))
class Audit(db.Model):
    id=db.Column(db.Integer,primary_key=True); username=db.Column(db.String(80)); action=db.Column(db.String(255)); created_at=db.Column(db.DateTime,default=datetime.utcnow)

ROLES=['Administrator','Farm Manager','Farm Supervisor','Driver']
def current_user(): return User.query.get(session.get('uid')) if session.get('uid') else None
def audit(action):
    u=current_user(); db.session.add(Audit(username=u.username if u else 'system',action=action)); db.session.commit()
def role_required(*roles):
    u=current_user(); return u and u.active and u.role in roles

def active_rate(d):
    r=Rate.query.filter(Rate.effective_from<=d, db.or_(Rate.effective_to==None,Rate.effective_to>=d)).order_by(Rate.effective_from.desc()).first()
    return Decimal(r.rate) if r else Decimal('0')

@app.context_processor
def inject(): return {'user':current_user(),'today':date.today()}
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=User.query.filter_by(username=request.form['username']).first()
        if u and u.active and check_password_hash(u.password,request.form['password']): session['uid']=u.id; return redirect(url_for('dashboard'))
        flash('Invalid login details')
    return render_template('login.html')
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))
@app.route('/')
def dashboard():
    if not current_user(): return redirect(url_for('login'))
    todaykg=sum((x.kg for x in Plucking.query.filter_by(work_date=date.today(),status='Verified')),Decimal('0'))
    month=date.today().strftime('%Y-%m'); p=Payroll.query.filter_by(month=month).all()
    return render_template('dashboard.html',workers=Worker.query.filter_by(status='Active').count(),todaykg=todaykg,monthlykg=sum((x.total_kg for x in p),Decimal('0')),payroll=sum((x.net for x in p),Decimal('0')),pending=Plucking.query.filter_by(status='Pending').count(),expenses=sum((x.amount for x in Expense.query.filter_by(status='Approved')),Decimal('0')))

@app.route('/workers',methods=['GET','POST'])
def workers():
    if not role_required('Administrator','Farm Manager','Farm Supervisor'): return ('Forbidden',403)
    if request.method=='POST':
        w=Worker(worker_no=request.form['worker_no'],name=request.form['name'],phone=request.form.get('phone'),id_no=request.form.get('id_no'),gender=request.form.get('gender'),section=request.form.get('section'),supervisor=request.form.get('supervisor'),payment_method=request.form.get('payment_method'))
        db.session.add(w); db.session.commit(); audit('Added worker '+w.worker_no); return redirect(url_for('workers'))
    return render_template('workers.html',workers=Worker.query.order_by(Worker.name).all())
@app.route('/plucking',methods=['GET','POST'])
def plucking():
    if not role_required('Administrator','Farm Manager','Farm Supervisor'): return ('Forbidden',403)
    if request.method=='POST':
        d=datetime.strptime(request.form['work_date'],'%Y-%m-%d').date(); kg=Decimal(request.form['kg']); rate=active_rate(d)
        if rate<=0: flash('Set an effective tea rate before recording plucking.'); return redirect(url_for('plucking'))
        x=Plucking(work_date=d,worker_id=int(request.form['worker_id']),section=request.form.get('section'),kg=kg,rate=rate,amount=kg*rate,status='Pending'); db.session.add(x); db.session.commit(); audit('Recorded plucking for worker '+str(x.worker_id)); return redirect(url_for('plucking'))
    return render_template('plucking.html',workers=Worker.query.filter_by(status='Active').all(),rows=Plucking.query.order_by(Plucking.work_date.desc()).limit(300).all())
@app.route('/plucking/<int:i>/verify')
def verify_plucking(i):
    if not role_required('Administrator','Farm Manager','Farm Supervisor'): return ('Forbidden',403)
    x=Plucking.query.get_or_404(i); x.status='Verified'; x.verified_by=current_user().username; db.session.commit(); audit('Verified plucking '+str(i)); return redirect(url_for('plucking'))
@app.route('/rates',methods=['GET','POST'])
def rates():
    if not role_required('Administrator','Farm Manager'): return ('Forbidden',403)
    if request.method=='POST': db.session.add(Rate(rate=Decimal(request.form['rate']),effective_from=datetime.strptime(request.form['from'],'%Y-%m-%d').date())); db.session.commit(); audit('Added tea rate'); return redirect(url_for('rates'))
    return render_template('rates.html',rates=Rate.query.order_by(Rate.effective_from.desc()).all())

@app.route('/payroll',methods=['GET','POST'])
def payroll():
    if not role_required('Administrator','Farm Manager'): return ('Forbidden',403)
    month=request.args.get('month',date.today().strftime('%Y-%m'))
    if request.method=='POST':
        month=request.form['month']; start=datetime.strptime(month+'-01','%Y-%m-%d').date();
        # rebuild only Draft payroll; approved/paid records are protected
        for w in Worker.query.filter_by(status='Active').all():
            if Payroll.query.filter_by(worker_id=w.id,month=month,status='Approved').first() or Payroll.query.filter_by(worker_id=w.id,month=month,status='Paid').first(): continue
            rows=Plucking.query.filter_by(worker_id=w.id,status='Verified').filter(Plucking.work_date>=start,Plucking.work_date< (date(start.year+1,1,1) if start.month==12 else date(start.year,start.month+1,1))).all()
            gross=sum((r.amount for r in rows),Decimal('0')); kg=sum((r.kg for r in rows),Decimal('0'))
            adv=sum((a.amount for a in Advance.query.filter_by(worker_id=w.id).filter(Advance.advance_date>=start,Advance.advance_date< (date(start.year+1,1,1) if start.month==12 else date(start.year,start.month+1,1))).all()),Decimal('0'))
            ded=sum((a.amount for a in Deduction.query.filter_by(worker_id=w.id).filter(Deduction.deduction_date>=start,Deduction.deduction_date< (date(start.year+1,1,1) if start.month==12 else date(start.year,start.month+1,1))).all()),Decimal('0'))
            x=Payroll.query.filter_by(worker_id=w.id,month=month).first() or Payroll(worker_id=w.id,month=month); x.total_kg=kg;x.gross=gross;x.advances=adv;x.deductions=ded;x.net=gross-adv-ded;x.status='Draft';db.session.add(x)
        db.session.commit(); audit('Generated payroll '+month); return redirect(url_for('payroll',month=month))
    return render_template('payroll.html',month=month,rows=Payroll.query.filter_by(month=month).order_by(Payroll.net.desc()).all())
@app.route('/payroll/<int:i>/approve')
def approve_payroll(i):
    if not role_required('Administrator','Farm Manager'): return ('Forbidden',403)
    x=Payroll.query.get_or_404(i); x.status='Approved'; db.session.commit(); audit('Approved payroll '+str(i)); return redirect(url_for('payroll',month=x.month))
@app.route('/payroll/<int:i>/pay',methods=['POST'])
def pay_payroll(i):
    if not role_required('Administrator','Farm Manager'): return ('Forbidden',403)
    x=Payroll.query.get_or_404(i)
    if x.status!='Approved': flash('Only approved payroll can be paid.'); return redirect(url_for('payroll',month=x.month))
    x.status='Paid';x.paid_at=datetime.utcnow();x.payment_ref=request.form.get('reference');db.session.commit();audit('Paid payroll '+str(i));return redirect(url_for('payroll',month=x.month))

@app.route('/advances',methods=['GET','POST'])
def advances():
    if not role_required('Administrator','Farm Manager'): return ('Forbidden',403)
    if request.method=='POST': db.session.add(Advance(worker_id=int(request.form['worker_id']),amount=Decimal(request.form['amount']),note=request.form.get('note')));db.session.commit();audit('Recorded worker advance');return redirect(url_for('advances'))
    return render_template('advances.html',workers=Worker.query.filter_by(status='Active').all(),rows=Advance.query.order_by(Advance.advance_date.desc()).all())
@app.route('/expenses',methods=['GET','POST'])
def expenses():
    if not role_required('Administrator','Farm Manager'): return ('Forbidden',403)
    if request.method=='POST': db.session.add(Expense(category=request.form['category'],description=request.form.get('description'),amount=Decimal(request.form['amount']),expense_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),status='Pending'));db.session.commit();audit('Recorded expense');return redirect(url_for('expenses'))
    return render_template('expenses.html',rows=Expense.query.order_by(Expense.expense_date.desc()).all())
@app.route('/expenses/<int:i>/approve')
def approve_expense(i):
    if not role_required('Administrator','Farm Manager'): return ('Forbidden',403)
    x=Expense.query.get_or_404(i);x.status='Approved';x.approved_by=current_user().username;db.session.commit();audit('Approved expense '+str(i));return redirect(url_for('expenses'))
@app.route('/attendance',methods=['GET','POST'])
def attendance():
    if not role_required('Administrator','Farm Manager','Farm Supervisor'): return ('Forbidden',403)
    if request.method=='POST': db.session.add(Attendance(worker_id=int(request.form['worker_id']),attend_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),status=request.form['status']));db.session.commit();return redirect(url_for('attendance'))
    return render_template('attendance.html',workers=Worker.query.filter_by(status='Active').all(),rows=Attendance.query.order_by(Attendance.attend_date.desc()).limit(300).all())
@app.route('/vehicles',methods=['GET','POST'])
def vehicles():
    if not role_required('Administrator','Farm Manager','Driver'): return ('Forbidden',403)
    if request.method=='POST': db.session.add(Vehicle(reg_no=request.form['reg_no'],model=request.form.get('model'),driver=request.form.get('driver')));db.session.commit();audit('Added vehicle');return redirect(url_for('vehicles'))
    return render_template('vehicles.html',rows=Vehicle.query.all())
@app.route('/trips',methods=['GET','POST'])
def trips():
    if not role_required('Administrator','Farm Manager','Driver'): return ('Forbidden',403)
    if request.method=='POST': db.session.add(Trip(trip_date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),vehicle_id=int(request.form['vehicle_id']),driver=request.form['driver'],pickup=request.form['pickup'],destination=request.form['destination'],kg=Decimal(request.form['kg']),reference=request.form.get('reference')));db.session.commit();audit('Recorded transport trip');return redirect(url_for('trips'))
    return render_template('trips.html',rows=Trip.query.order_by(Trip.trip_date.desc()).all(),vehicles=Vehicle.query.all())
@app.route('/audit')
def audit_page():
    if not role_required('Administrator','Farm Manager'): return ('Forbidden',403)
    return render_template('audit.html',rows=Audit.query.order_by(Audit.created_at.desc()).limit(500).all())

@app.cli.command('init-db')
def init_db():
    db.create_all();
    if not User.query.filter_by(username='admin').first(): db.session.add(User(username='admin',password=generate_password_hash(os.getenv('ADMIN_PASSWORD','Admin@12345')),role='Administrator'))
    db.session.commit(); print('Database initialized. Default admin: admin / Admin@12345 (change immediately).')

@app.route('/health')
def health(): return jsonify(status='ok',farm='KAPKOSGEI OUTGROWERS FARM')
if __name__=='__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')))
