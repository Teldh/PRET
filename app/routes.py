# -*- coding: utf-8 -*-
from flask import render_template, redirect, flash, url_for, json
import os
from app import app, db
from app.forms import LoginForm, RevisionForm, RegisterForm, BaselineForm, BaselineResultsForm, ComparisonForm, AnalysisForm, PreAnnotatorForm, PreVisualizationForm, UploadTerminologyForm, GoldStandardForm, TextDeleteForm, TextDownloadForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Book, Author, Conll, goldStandard, partialAnnotations, Terminology, bookStructure, Baseline_Methods, Annotations, Annotation_user, Terminology_reference, partialAnnotations, goldStandard, Bs_status, Terminology_status, Revision_type, Revised_annotations, Revision_tag, Revision_status, Bs_threshold, Burst_params, Burst_params_allen, Burst_results, Burst_rel_allen
from flask import request, jsonify, make_response
from werkzeug.urls import url_parse
from app import utils, wikipedia, Method_01, Method_02, Method_03, Method_04, Method_05, Method_06, temp, conll_processor_2, computeAgreement, agreement_kappa_no_inv_all_paths, agreement_kappa_conta_inv_all_paths, agreement_kappa_fleiss
import re
from threading import Thread
import sys
import io
import csv
 
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, surname=form.surname.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("You are now a registered user!", "succes")
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/text_delete', methods=['GET','POST'])
@login_required
def text_delete():
    form = TextDeleteForm()
    cap_lista = Conll.query.all()
    form.book_cap.choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + " -- Chapter: " + str(cap.cap))) for cap in cap_lista]
    if form.validate_on_submit():
        value = form.book_cap.data.split(",")
        bid = value[0]
        cap = value[1]

        '''db.session.execute(
            'DELETE * FROM annotations JOIN annotation_user WHERE annotations.bid = bid AND annotations.cap = cap',
            {"bid": bid,"cap":cap}
        )'''
        '''db.session.query(Annotations). \
            filter(Annotations.aid == Annotation_user.aid,
                   bid == bid,
                   cap == cap). \
            delete(synchronize_session=False)'''

        annotations = Annotations.query.filter_by(bid=bid, cap=cap).all()
        for ann in annotations:
            ann_users = Annotation_user.query.filter_by(aid=ann.aid).all()
            for a in ann_users:
                revised_anns = Revised_annotations.query.filter_by(ann_user_id=a.ann_user_id)
                for r in revised_anns:
                    db.session.delete(r)
                db.session.delete(a)
            db.session.delete(ann)

        structure = bookStructure.query.filter_by(bid=bid).all()
        for s in structure:
            if s.section.startswith(cap + ".") or s.section == cap:
                db.session.delete(s)

        methods = Baseline_Methods.query.filter_by(bid=bid, cap=cap).all()
        for m in methods:
            db.session.delete(m)

        status = Bs_status.query.filter_by(bid=bid, cap=cap).all()
        for m in status:
            db.session.delete(m)

        bs_threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap).all()
        for m in bs_threshold:
            db.session.delete(m)

        toDelete=Burst_params.query.filter_by(bid=bid, cap=cap).first()
        if toDelete:
            db.session.delete(toDelete)

        toDelete = Burst_params_allen.query.filter_by(bid=bid, cap=cap).all()
        for m in toDelete:
            db.session.delete(m)

        toDelete = Burst_rel_allen.query.filter_by(bid=bid, cap=cap).all()
        for m in toDelete:
            db.session.delete(m)

        toDelete = Burst_results.query.filter_by(bid=bid, cap=cap).all()
        for m in toDelete:
            db.session.delete(m)

        db.session.delete(Conll.query.filter_by(bid=bid, cap=cap).first())

        toDelete = goldStandard.query.filter_by(bid=bid, cap=cap).first()
        if toDelete:
            db.session.delete(toDelete)

        toDelete = partialAnnotations.query.filter_by(bid=bid, cap=cap).first()
        if toDelete:
            db.session.delete(toDelete)


        toDelete = Revision_status.query.filter_by(bid=bid, cap=cap).all()
        for m in toDelete:
            db.session.delete(m)

        toDelete = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
        for m in toDelete:
            db.session.delete(m)

        db.session.delete(Terminology_status.query.filter_by(bid=bid, cap=cap).first())

        db.session.commit()

        cap_lista = Conll.query.all()
        form.book_cap.choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (
            db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + " -- Chapter: " + str(
            cap.cap))) for cap in cap_lista]

        flash("Text deleted", "success")

    return render_template('text_delete.html', form=form)

@app.route('/text_download', methods=['GET','POST'])
@login_required
def text_download():
    form = TextDownloadForm()
    cap_lista = Conll.query.all()
    form.book_cap.choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + " -- Chapter: " + str(cap.cap))) for cap in cap_lista]
    if form.validate_on_submit():
        value = form.book_cap.data.split(",")
        bid = value[0]
        cap = value[1]

        conll = Conll.query.filter_by(bid=bid, cap=cap).first().conll

        output = make_response(conll)
        output.headers["Content-Disposition"] = "attachment; filename=conll.txt"
        output.headers["Content-type"] = "text/plain"

        print(output)
        return output

    return render_template('text_download.html', form=form)



@app.route('/term_upload', methods=['GET','POST'])
@login_required
def term_upload():
    form =  UploadTerminologyForm()
    cap_lista = Conll.query.join(bookStructure, bookStructure.bid == Conll.bid).filter(bookStructure.uid == current_user.uid).all()

    cap_lista = [x for x in cap_lista if (Terminology_status.query.filter_by(cap = x.cap, bid = x.bid).first().status == "ready" or Terminology_status.query.filter_by(cap = x.cap, bid = x.bid).first().status == "failed")]
    form.book_cap.choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + " -- Chapter: " + str(cap.cap))) for cap in cap_lista]
    if form.validate_on_submit():
        try:
            value = form.book_cap.data.split(",")
            bid = value[0]
            cap = value[1]

            stato = Terminology_status.query.filter_by(bid=bid, cap=cap).first()
            stato.status = "running"
            db.session.commit()

            f = request.files['text']
            content = f.stream.read().decode("UTF8")
            terms = [term for term in content.splitlines() if term]
            print(len(terms))
            text = utils.conll_to_text0(Conll.query.filter_by(cap=cap, bid=bid).first().conll, 0)
            wikipedia.initialize_page(text, terms, bid, cap)
            '''for word in [x.lower() for x in terms if x]:
                if (Terminology.query.filter_by(lemma=word).first()):
                    tid = Terminology.query.filter_by(lemma=word).first().tid
                    if not(Terminology_reference.query.filter_by(tid=tid, cap=cap, bid=bid).first()):
                        term_ref = Terminology_reference(tid=tid, cap=cap, bid=bid)
                        db.session.add(term_ref)'''

            # Metto stato dei metodi in ready
            for i in range(1,7):
                row = Bs_status.query.filter_by(bid=bid, cap=cap, method=i).first()
                row.status = "ready"

            # Metto succeeded (caricata) come stato della terminologia
            stato = Terminology_status.query.filter_by(bid=bid, cap=cap).first()
            stato.status = "succeeded"
            flash("Terminology uploaded", "success")
            db.session.commit()
        except:
            stato = Terminology_status.query.filter_by(bid=bid, cap=cap).first()
            stato.status = "failed"
            print(sys.exc_info())
            flash("Failed, please retry using the terminology requirements", "danger")
            db.session.commit()

        libri = db.session \
            .query(Book.bid, Book.title, Terminology_status.cap, Terminology_status.status) \
            .join(bookStructure, (bookStructure.bid == Book.bid)) \
            .join(Terminology_status,
                  (Book.bid == Terminology_status.bid) & (Terminology_status.cap == bookStructure.section)) \
            .group_by(Book.title, Terminology_status.cap)

        return render_template('terminology_upload.html', form=form, file={'books': libri})

    libri = db.session\
        .query(Book.bid, Book.title, Terminology_status.cap, Terminology_status.status)\
        .join(bookStructure, (bookStructure.bid == Book.bid))\
        .join(Terminology_status, (Book.bid == Terminology_status.bid) & (Terminology_status.cap == bookStructure.section))\
        .group_by(Book.title, Terminology_status.cap)

    return render_template('terminology_upload.html', form=form, file={'books': libri})


@app.route('/baseline', methods=['GET','POST'])
@login_required
def baseline():
    form = BaselineForm()
    cap_lista = Conll.query.all()
    form.book_cap.choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + " -- Chapter: " + str(cap.cap))) for cap in cap_lista]
    if cap_lista:

        if form.validate_on_submit():
            value = form.book_cap.data.split(",")
            bid = value[0]
            cap = value[1]
            conll = Conll.query.filter_by(bid=bid, cap=cap).first().conll
            words_id = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
            words = [Terminology.query.filter_by(tid=word_id.tid).first() for word_id in words_id]

            if form.baseline_method.data == "1":
                stato =  Bs_status.query.filter_by(cap = cap, bid = bid, method=1).first()

                if stato.status == "not ready":
                    message = "Terminology not uploaded yet"
                    flash(message, "warning")

                elif stato.status != "succeeded" and stato.status != "running" and stato.status != "not ready":
                    words = [word.lemma for word in words]
                    baseline = Method_01.Method_1(words, bid, cap)
                    try:
                        load(baseline.method_1())
                    except:
                        flash("Failed", "danger")
                else:
                    message = "You cannot launch a " + stato.status + " method"
                    flash(message, "warning")

            elif form.baseline_method.data == "2":
                stato = Bs_status.query.filter_by(cap=cap, bid=bid, method=2).first()
                if stato.status == "not ready":
                    message = "Terminology not uploaded yet"
                    flash(message, "warning")

                elif stato.status != "succeeded" and stato.status != "running":
                    words = [word.lemma for word in words]
                    text = utils.conll_to_text0(conll, 0)
                    baseline = Method_02.Method_2(words, conll, text, bid, cap)
                    try:
                        load(baseline.method_2())
                    except:
                        flash("Failed", "danger")
                else:
                    message = "You cannot launch a " + stato.status + " method"
                    flash(message, "warning")

            elif form.baseline_method.data == "3":
                stato = Bs_status.query.filter_by(cap=cap, bid=bid, method=3).first()
                if stato.status == "not ready":
                    message = "Terminology not uploaded yet"
                    flash(message, "warning")

                elif stato.status != "succeeded" and stato.status != "running":
                    title = [word.wiki_url for word in words]
                    words = [word.lemma for word in words]
                    dictionary = dict(zip(words, title))
                    threshold = form.threshold.data
                    try:
                        load(Method_03.method_3(dictionary, bid, cap, threshold))
                    except:
                        flash("Failed", "danger")
                else:
                    message = "You cannot launch a " + stato.status + " method"
                    flash(message, "warning")


            elif form.baseline_method.data == "4":
                stato = Bs_status.query.filter_by(cap=cap, bid=bid, method=4).first()
                if stato.status == "not ready":
                    message = "Terminology not uploaded yet"
                    flash(message, "warning")

                elif stato.status != "succeeded" and stato.status != "running":
                    title = [word.wiki_url for word in words]
                    words = [word.lemma for word in words]
                    #dictionary = dict(zip(words[0:int(len(words)*0.2)], title[0:int(len(words)*0.2)]))
                    dictionary = dict(zip(words[0:int(len(words))], title[0:int(len(words))]))
                    try:
                        load(Method_04.method_4(dictionary, bid, cap))
                    except:
                        flash("Failed", "danger")
                else:
                    message = "You cannot launch a " + stato.status + " method"
                    flash(message, "warning")

            elif form.baseline_method.data == "5":
                stato = Bs_status.query.filter_by(cap=cap, bid=bid, method=5).first()
                if stato.status == "not ready":
                    message = "Terminology not uploaded yet"
                    flash(message, "warning")

                elif stato.status != "succeeded" and stato.status != "running":
                    threshold = form.threshold.data
                    words = [word.lemma for word in words]
                    sections = bookStructure.query.filter_by(bid=bid).all()
                    chapter = [chap for chap in sections if chap.section.startswith(cap + ".")]
                    text = {}
                    for i, chap in enumerate(chapter):
                        if i+1 < len(chapter):
                            text[chap.section] = (utils.conll_to_text1(conll, chap.sentence, chapter[i+1].sentence))
                        else:
                            text[chap.section] = (utils.conll_to_text0(conll, chap.sentence))
                    baseline = Method_05.Method_5(words, text, bid, cap, threshold)
                    try:
                        load(baseline.method_5())
                    except:
                        flash("Failed", "danger")
                else:
                    message = "You cannot launch a " + stato.status + " method"
                    flash(message, "warning")

            elif form.baseline_method.data == "6":
                stato = Bs_status.query.filter_by(cap=cap, bid=bid, method=6).first()
                if stato.status == "not ready":
                    message = "Terminology not uploaded yet"
                    flash(message, "warning")

                elif stato.status != "succeeded" and stato.status != "running":
                    words = [word.lemma for word in words]
                    text = utils.conll_to_text0(conll, 0)
                    threshold = form.threshold.data

                    #il metodo è rilanciabile solo se uso parametri diversi
                    already_launched = False
                    last_params_used = {}

                    if Bs_status.query.filter_by(cap=cap, bid=bid, method=6).first().status == "modifiable":
                        already_launched = True
                        params = Burst_params.query.filter_by(cap=cap, bid=bid).first()
                        last_threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=6).first().threshold

                        last_params_used = {'threshold': last_threshold, 'S':params.s,'gamma':params.gamma,'level':params.level}
                        allen_params = Burst_params_allen.query.filter_by(cap=cap, bid=bid).all()

                        for allen in allen_params:
                            last_params_used.update({str(allen.type): allen.weight})


                    if form.default.data:
                        baseline = Method_06.Method_6(text, words, conll,  bid, cap)

                        # usa i parametri di default
                        new_params = {'threshold': threshold,'S':1.05, 'gamma':0.0001, 'level':1,'equals': 2,'before': 5, 'after': 0, 'meets': 3,
                                      'met-by': 0,'overlaps': 7, 'overlapped-by': 1,'during': 7, 'includes': 7,'starts': 4,
                                      'started-by': 2, 'finishes': 2, 'finished-by': 8}
                    else:
                        allen_weights = {'equals': form.equals.data, 'before': form.before.data, 'after': form.after.data,
                                         'meets': form.meets.data, 'met-by': form.metby.data,'overlaps': form.overlaps.data,
                                         'overlapped-by': form.overlappedby.data, 'during': form.during.data,
                                         'includes': form.includes.data, 'starts': form.starts.data,
                                         'started-by': form.startedby.data, 'finishes': form.finishes.data,
                                         'finished-by': form.finishedby.data}

                        baseline = Method_06.Method_6(text, words, conll, bid, cap, form.s.data, form.gamma.data,
                                                      form.level.data, allen_weights,form.use_inverses.data,
                                                      form.max_gap.data)

                        new_params = {'threshold': threshold,'S':form.s.data, 'gamma':form.gamma.data, 'level':form.level.data}
                        new_params.update(allen_weights)

                    try:
                        if already_launched and last_params_used == new_params:
                            message = "These parameters have already been used"
                            flash(message, "warning")
                        else:
                            load(baseline.method_6())

                            #salvo threshold
                            t = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=6).first()
                            if not t:
                                t = Bs_threshold(bid=bid, cap=cap, method=6, threshold=threshold)
                                db.session.add(t)
                            else:
                                t.threshold = threshold

                            db.session.commit()


                    except ValueError as e:
                        flash("Error: "+ str(e), "danger")

                else:
                    message = "You cannot launch a " + stato.status + " method"
                    flash(message, "warning")
        else:
            if request.method == 'POST':
                message = "Insert all parameters"
                flash(message, "warning")


    return render_template('baseline.html', form=form)


@app.route('/baseline/<book>')
@login_required
def get_status_baseline(book):
    # Prendo gli stati di <book> e creo il json
    # baseline.html userà questo json per scrivere gli stati nel form (succeeded ✔) etc

    bid = book.split(",")[0]
    cap = book.split(",")[1]

    stati = Bs_status.query.filter_by(cap=cap, bid=bid).all()
    statiList = []

    if stati:
        for stato in stati:
            if stato.status == "ready":
                icon = '▶️'
            elif stato.status == "succeeded" or stato.status == "modifiable":
                icon = "✔"
            elif stato.status == "running":
                icon = "⚡"
            elif stato.status == "failed":
                icon = "❌"
            elif stato.status == "not ready":
                icon = ""
            statoObj = {}
            statoObj["id"] = int(stato.method)
            statoObj["stato"] = stato.status + " " + icon
            statiList.append(statoObj)

    return jsonify({'stati': statiList})

@app.route('/baseline_burst_status/<book>')
@login_required
def get_status_burst(book):
    # baseline.html userà questo json per stamapare i parametri usati in burst

    bid = book.split(",")[0]
    cap = book.split(",")[1]

    stato = Bs_status.query.filter_by(cap=cap, bid=bid, method=6).first().status

    return jsonify({'stato': stato})

@app.route('/baseline_burst_params/<book>')
@login_required
def get_status_params(book):
    # baseline.html userà questo json per stamapare i parametri usati in burst

    bid = book.split(",")[0]
    cap = book.split(",")[1]

    params = Burst_params.query.filter_by(cap=cap, bid=bid).first()


    return jsonify({'s': params.s, 'gamma':params.gamma, 'level':params.level})

@app.route('/baseline_results', methods=['GET','POST'])
@login_required
def baseline_results():
    form = BaselineResultsForm()
    cap_lista = Conll.query.all()
    if cap_lista:
        form.book_cap.choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + " -- Chapter: " + str(cap.cap))) for cap in cap_lista]
        if form.validate_on_submit():
            value = form.book_cap.data.split(",")
            bid = value[0]
            cap = value[1]

            if form.baseline_method.data == "1":
                relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap, m1 = 1).all()
                return render_template('baseline_visualization.html',file = {'bid':bid, 'cap':cap, 'relations':relations,'metodo':1})
            elif form.baseline_method.data == "2":
                relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap, m2 = 1).all()
                return render_template('baseline_visualization.html',file = {'bid':bid, 'cap':cap,'relations':relations,'metodo':2})
            elif form.baseline_method.data == "3":
                relations =  db.session.query(Baseline_Methods).filter((Baseline_Methods.bid == bid) & (Baseline_Methods.cap == cap) & (Baseline_Methods.m3 != None)).order_by(Baseline_Methods.m3).all()
                return render_template('baseline_visualization.html',file = {'bid':bid, 'cap':cap,'relations':relations,'metodo':3})
            elif form.baseline_method.data == "4":
                relations = db.session.query(Baseline_Methods).filter((Baseline_Methods.bid == bid) & (Baseline_Methods.cap == cap) & (Baseline_Methods.m4 == 1)).order_by(Baseline_Methods.m4).all()
                return render_template('baseline_visualization.html',file = {'bid':bid, 'cap':cap,'relations':relations,'metodo':4})
            elif form.baseline_method.data == "5":
                relations = db.session.query(Baseline_Methods).filter((Baseline_Methods.bid == bid) & (Baseline_Methods.cap == cap) & (Baseline_Methods.m5 != None)).order_by(Baseline_Methods.m5).all()
                return render_template('baseline_visualization.html',file = {'bid':bid, 'cap':cap,'relations':relations,'metodo':5})
            elif form.baseline_method.data == "6":
                relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap).order_by(Baseline_Methods.m6.desc()).all()
                return render_template('baseline_visualization.html',file = {'bid':bid, 'cap':cap,'relations':relations,'metodo':6})

    return render_template('baseline_results.html', form=form)


@app.route('/download_method_results/<dati>', methods= ['GET'])
@login_required
def download_method_results(dati):
    dati = dati.split(",")

    bid = dati[0]
    cap = dati[1]
    method = dati[2]

    si = io.StringIO()
    cw = csv.writer(si)

    if method == "1":
        relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap, m1=1).all()
        for r in relations:
            cw.writerow([r.lemma2, r.lemma1])

    elif method == "2":
        relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap, m2=1).all()
        for r in relations:
            cw.writerow([r.lemma2, r.lemma1])

    elif method == "3":
        relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap).order_by(Baseline_Methods.m3).all()
        for r in relations:
            cw.writerow([r.lemma2, r.lemma1, r.m3])

    elif method == "4":
        relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap, m4=1).order_by(Baseline_Methods.m4).all()
        for r in relations:
            cw.writerow([r.lemma2, r.lemma1])

    elif method == "5":
        relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap).order_by(Baseline_Methods.m5).all()
        for r in relations:
            cw.writerow([r.lemma2, r.lemma1, r.m5])

    elif method == "6":
        relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap).order_by(Baseline_Methods.m6.desc()).all()
        for r in relations:
            cw.writerow([r.lemma2, r.lemma1, r.m6])


    #cw.writerows(list)

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename="+method+"_results.csv"
    output.headers["Content-type"] = "text/csv"

    print(output)
    return output

@app.route('/analysis', methods=['GET','POST'])
@login_required
def analysis():
    form = AnalysisForm()
    cap_lista = Conll.query.all()
    if cap_lista:
        form.book_cap.choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + "-- Chapter: " + str(cap.cap))) for cap in cap_lista]

        choices = utils.get_list_annotations(cap_lista[0].bid, cap_lista[0].cap)

        for c in choices:
            form.annotation_1.choices.append((c['id'], c['name']))
            form.annotation_2.choices.append((c['id'], c['name']))

        if form.validate_on_submit():
            value = form.book_cap.data.split(",")
            bid = value[0]
            cap = value[1]
            conll = Conll.query.filter_by(bid=bid, cap=cap).first().conll
            sentences = bookStructure.query.filter_by(bid=bid).all()
            sentences = [sentence for sentence in sentences if str(sentence.section).startswith(str(cap) + ".")]

            if form.analysis_type.data == "2":
                #linguistic analysis si può fare per le annotazioni, per le gold e solo per il metodo due
                if "gold" in str(form.annotation_1.data) or "uid" in str(form.annotation_1.data) or form.annotation_1.data in ["2"]:

                    if "gold" in str(form.annotation_1.data):
                        json_relations = utils.linguistic_json_gold(bid, cap, form.annotation_1.data.split(".")[1])
                    elif form.annotation_1.data == "2":
                        json_relations = utils.linguistic_json_method2(bid, cap)
                    else:
                        json_relations = utils.linguistic_json(bid, cap, form.annotation_1.data.split(".")[1])
                    #print(json_relations)
                    json_relations = json.dumps(json_relations)
                    # Gets all the words involveded in the book bid and chapter cap
                    words_id = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
                    words = [Terminology.query.filter_by(tid=word_id.tid).first().lemma for word_id in words_id]
                    conll_obj = Conll.query.filter_by(bid=bid, cap=cap).first()
                    conll_processed = conll_obj.conll_processed
                    conll = utils.conll_annotation(conll_obj.conll)
                    sentences = bookStructure.query.filter_by(bid=bid).all()
                    sentences = [x.sentence for x in sentences if x.section.startswith(cap)]
                    conll_processed, sentList, tok_to_concept, concept_to_tok = conll_processor_2.conll_processor(conll_processed, 'PROVA', sentences, words)
                    return render_template('linguistic_analysis.html', file = {'json' : json_relations, 'concepts' : words,  'conll' : conll, 'tagged' : conll_processed, 'concepts' : words, 'tok_to_concept' : tok_to_concept, 'concept_to_tok' : concept_to_tok, 'sentence' : sentList})

            elif form.analysis_type.data == "1":
                #Data summary
                # Gets all the words involveded in the book bid and chapter cap
                words_tid = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
                words = [Terminology.query.filter_by(tid=word.tid).first().lemma for word in words_tid]
                if("gold" in str(form.annotation_1.data)):
                    dfAnnotation, df, metrics, words =  utils.create_dfAnnotation(bid, cap, form.annotation_1.data, conll, words)
                    dfAnnotation = dfAnnotation.drop(columns=["weight"])
                    print(dfAnnotation)
                    metrics = utils.data_summary(dfAnnotation, df, metrics, form.annotation_1.data)
                else:
                    dfAnnotation, df, metrics, words = utils.data_analysis(conll, words, sentences, bid, cap, form.annotation_1.data)
                    if form.annotation_1.data.startswith("uid"):
                        dfAnnotation = dfAnnotation.drop(columns=["weight"])
                    print(dfAnnotation)
                    metrics = utils.data_summary(dfAnnotation, df, metrics, form.annotation_1.data)

                if form.annotation_1.data in ["1", "2", "3", "4", "5", "6"]:
                    # calcolare accuracy, precision, f1 score per i metodi di estrazioni automatica, rispetto alla gold

                    if form.annotation_2.data != "Default":
                        gold = form.annotation_2.data.split(".")[1]
                        method = form.annotation_1.data
                        data = "gold." + str(gold)
                        dfAnnotation_Gold, df_gold, metrics_gold, words_gold = utils.create_dfAnnotation(bid, cap, data, conll, words)

                        accuracy, precision, recall, F1 = utils.scores(bid, cap, dfAnnotation, dfAnnotation_Gold, method)

                        # per il metodo di Burst devo dare la possibilita del download della summary
                        if method == '6':
                            return render_template('data_summary.html', file=metrics, accuracy=round(accuracy,3),
                                               precision=round(precision,3), recall=round(recall,3), F1=round(F1,3),
                                               bid=bid, cap=cap, gid=gold)
                        else:
                            return render_template('data_summary.html', file=metrics, accuracy=round(accuracy, 3),
                                                   precision=round(precision, 3), recall=round(recall, 3),
                                                   F1=round(F1, 3))

                return render_template('data_summary.html', file = metrics)

            elif form.analysis_type.data == "3":
                # Gets all the words involveded in the book bid and chapter cap
                words_tid = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
                words = [Terminology.query.filter_by(tid=word.tid).first().lemma for word in words_tid]
                if form.annotation_1.data not in ["1", "2", "3", "4", "5"] and form.annotation_2.data not in ["1", "2", "3", "4", "5"]:
                    uid1 = form.annotation_1.data.split(".")[1]
                    uid2 = form.annotation_2.data.split(".")[1]

                    all_combs = computeAgreement.createAllComb(words)
                    file1 = utils.agreement_json(bid, cap, uid1)
                    file2 = utils.agreement_json(bid, cap, uid2)

                    term_pairs={uid1:[], uid2:[]}
                    term_pairs[uid1], all_combs = computeAgreement.createUserRel(file1, all_combs)
                    term_pairs[uid2], all_combs = computeAgreement.createUserRel(file2, all_combs)

                    metrics = computeAgreement.creaCoppieAnnot(uid1, uid2, term_pairs, all_combs)

                    # Calcolo agreement kappa no-inv all paths
                    term_pairs = {uid1: [], uid2: []}
                    term_pairs_tuple = {uid1: [], uid2: []}
                    term_pairs[uid1], all_combs, term_pairs_tuple[uid1] = agreement_kappa_no_inv_all_paths.createUserRel(file1, all_combs)
                    term_pairs[uid2], all_combs, term_pairs_tuple[uid2] = agreement_kappa_no_inv_all_paths.createUserRel(file2, all_combs)

                    print(term_pairs)
                    #coppieannotate, conteggio = agreement_kappa_no_inv_all_paths.creaCoppieAnnot(uid1, uid2, term_pairs, all_combs, term_pairs_tuple)
                    #no_inv = agreement_kappa_no_inv_all_paths.computeK(conteggio, all_combs)
                    # Calcolo agreement kappa conta-inv all paths
                    coppieannotate, conteggio = agreement_kappa_conta_inv_all_paths.creaCoppieAnnot(uid1, uid2, term_pairs, all_combs,term_pairs_tuple)

                    print("conteggio: ",conteggio)
                    #if uid1!=uid2:
                    metrics["kappa"] = round(agreement_kappa_conta_inv_all_paths.computeK(conteggio, all_combs),3)
                    #else:
                        #metrics["kappa"] = 1


                    user1 = User.query.filter_by(uid=uid1).first()
                    name1 = user1.name + " " + user1.surname
                    user2 = User.query.filter_by(uid=uid2).first()
                    name2 = user2.name + " " + user2.surname


                    return render_template('agreement.html', file=metrics, rel1=name1, rel2=name2)
            elif form.analysis_type.data == "4":
                words_tid = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
                words = [Terminology.query.filter_by(tid=word.tid).first().lemma for word in words_tid]
                all_combs = computeAgreement.createAllComb(words)

                # Calcolo Fleiss
                # prendo tutti gli utenti che hanno annotato questo libro
                annotationRel = Annotations.query.filter_by(cap=cap, bid=bid).all()
                users = []
                for annotations in annotationRel:
                    userz = Annotation_user.query.filter_by(aid=annotations.aid).all()
                    for user in userz:
                        user = user.uid
                        if user and user not in users:
                            users.append(user)

                # per ogni utente
                term_pairs = {}
                for user in users:
                    file = utils.agreement_json(bid, cap, user)
                    term_pairs[user] = computeAgreement.createUserRel(file, all_combs)[0]

                fleiss = agreement_kappa_fleiss.computeFleiss(term_pairs, all_combs)

                return render_template('fleiss.html', fleiss=round(fleiss, 3))

            else:
                return redirect(url_for('index'))
    return render_template('analysis.html', form=form)

@app.route('/analysis/<book>')
@login_required
def get_annotation(book):
    print(book)
    bid = book.split(",")[0]
    cap = book.split(",")[1]

    annotationList = utils.get_list_annotations(bid, cap)

    return jsonify({'annotation': annotationList})


@app.route('/download_burst_summary/<dati>', methods= ['GET'])
@login_required
def download_burst_summary(dati):
    dati = dati.split(",")

    bid = dati[0]
    cap = dati[1]
    gid = dati[2]
    accuracy = dati[3]
    precision = dati[4]
    recall = dati[5]
    F1 = dati[6]

    title = Book.query.filter_by(bid=bid).first().title

    annotationGold = goldStandard.query.filter_by(gid=gid).first()

    nomeGold = annotationGold.name
    gold = nomeGold

    burst_params = Burst_params.query.filter_by(bid=bid, cap=cap).first()

    list = [('book title',title),('chapter',cap),('gold',gold), ('accuracy',accuracy),('precision',precision),('recall',recall),
            ('F1 score',F1), ('S',burst_params.s),('gamma',burst_params.gamma),('Level', burst_params.level)]

    burst_params_allen = Burst_params_allen.query.filter_by(bid=bid, cap=cap).all()

    for p in burst_params_allen:
        list.append((p.type,p.weight))


    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerows(list)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=burst_results.csv"
    output.headers["Content-type"] = "text/csv"

    print(output)
    return output

        
@app.route('/comparison', methods=['GET','POST'])
@login_required
def comparison():
    form = ComparisonForm()
    cap_lista = Conll.query.all()
    form.book_cap.choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + " -- Chapter: " + str(cap.cap))) for cap in cap_lista]
    if cap_lista:
        choices = utils.get_list_annotations(cap_lista[0].bid, cap_lista[0].cap)

        for c in choices:
            form.comparison_1.choices.append((c['id'], c['name']))
            form.comparison_2.choices.append((c['id'], c['name']))

        if form.validate_on_submit():
            value = form.book_cap.data.split(",")
            bid = value[0]
            cap = value[1]
            conll = Conll.query.filter_by(bid=bid, cap=cap).first().conll
            sentences = bookStructure.query.filter_by(bid=bid).all()
            sentences = [sentence for sentence in sentences if str(sentence.section).startswith(str(cap) + ".")]
            # Gets all the words involveded in the book bid and chapter cap
            words_tid = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
            words = [Terminology.query.filter_by(tid=word.tid).first().lemma for word in words_tid]
            if("gold" in str(form.comparison_1.data)):
                dfAnnotation1, df, metrics, words =  utils.create_dfAnnotation(bid, cap, form.comparison_1.data, conll, words)
                dfAnnotation1 = dfAnnotation1.drop(columns=["weight"])
                metrics1 = utils.data_summary(dfAnnotation1, df, metrics, form.comparison_1.data)
            else:
                dfAnnotation1, df, metrics, words = utils.data_analysis(conll, words, sentences, bid, cap, form.comparison_1.data)
                if form.comparison_1.data.startswith("uid"):
                    dfAnnotation1 = dfAnnotation1.drop(columns=["weight"])
                metrics1 = utils.data_summary(dfAnnotation1, df, metrics, form.comparison_1.data)
            if("gold" in str(form.comparison_2.data)):
                dfAnnotation2, df, metrics, words =  utils.create_dfAnnotation(bid, cap, form.comparison_2.data, conll, words)
                dfAnnotation2 = dfAnnotation2.drop(columns=["weight"])
                metrics2 = utils.data_summary(dfAnnotation2, df, metrics, form.comparison_2.data)
            else:
                dfAnnotation2, df, metrics, words = utils.data_analysis(conll, words, sentences, bid, cap, form.comparison_2.data)
                if form.comparison_2.data.startswith("uid"):
                    dfAnnotation2 = dfAnnotation2.drop(columns=["weight"])
                metrics2 = utils.data_summary(dfAnnotation2, df, metrics, form.comparison_2.data)


            #se sono entrambi annotazioni di utenti devo tenere conto del peso e stamparli entrambi
            entrambi_utenti = form.comparison_1.data.startswith('uid') and form.comparison_2.data.startswith('uid')

            #se sono entrambi metodi automatici devo calcolare anche gli score rispetto alla gold
            # e le relazioni condivise con la gold
            entrambi_metodi = form.comparison_1.data in ["1","2","3","4","5","6"] \
                              and form.comparison_2.data in ["1","2","3","4","5","6"] and form.gold.data != "None"

            print(form.comparison_2.data)

            #se sono entrambi metodi e ho scelto una gold, prendo le relazioni della gold
            relazioni_gold = []
            if entrambi_metodi:
                dfAnnotation_gold, df_gold, metrics_gold, words_gold = utils.create_dfAnnotation(bid, cap, form.gold.data, conll, words)
                for row in dfAnnotation_gold.itertuples():
                    rel = (row.prerequisites, row.subsidiaries)
                    relazioni_gold.append(rel)


            relazioni1 = []

            #Prima annotazione, creo lista con (prereq, target) e weight se annotazione di utente
            if form.comparison_1.data.startswith('gold'):
                for row in dfAnnotation1.itertuples():
                    rel = (row.prerequisites, row.subsidiaries)
                    relazioni1.append(rel)
            else:
                relazioni1 = utils.getRelations(bid,cap,form.comparison_1.data)

            relazioni2 = []

            #Seconda annotazione, lista con (prereq, target, weight)
            if form.comparison_2.data.startswith('gold'):
                for row in dfAnnotation2.itertuples():
                    rel = (row.prerequisites, row.subsidiaries)
                    relazioni2.append(rel)
            else:
                relazioni2 = utils.getRelations(bid, cap, form.comparison_2.data)

            #relazioni condivise tra i due metodi/annotatori
            relazioni_condivise = []
            #relazioni condivise tra i due metodi e gold
            relazioni_condivise_gold = []
            relazioni_opposte = []

            for rel in relazioni1:
                for rel2 in relazioni2:
                    if rel[0] == rel2[0] and rel[1] == rel2[1]:

                        if entrambi_utenti:
                            r = {"prereq":rel[0], "target":rel[1], "weight1": rel[2], "weight2":rel2[2]}

                        else:
                            r = {"prereq":rel[0], "target":rel[1]}

                        g = {}
                        if entrambi_metodi:
                            for rel3 in relazioni_gold:
                                if rel[0] == rel3[0] and rel[1] == rel3[1]:
                                    g = {"prereq": rel[0], "target": rel[1]}
                                    relazioni_condivise_gold.append(g)

                        if g != r:
                            relazioni_condivise.append(r)

                    elif rel[0] == rel2[1] and rel[1] == rel2[0]:
                        r = {"lemma1": rel[0], "lemma2": rel[1]}
                        relazioni_opposte.append(r)

            # Prendo i nomi da stampare
            nomi = utils.get_list_annotations(bid,cap)

            nome1 = [a for a in nomi if str(a["id"]) == str(form.comparison_1.data)][0]["name"]
            nome2 = [b for b in nomi if str(b["id"]) == str(form.comparison_2.data)][0]["name"]


            # se confronto fra due metodi, devo calcolare gli score di entrambi i metodi rispetto alla gold
            if entrambi_metodi:
                gold = form.gold.data
                dfAnnotation_Gold, df_gold, metrics_gold, words_gold = utils.create_dfAnnotation(bid, cap, gold, conll, words)

                accuracy1, precision1, recall1, F1_1 = utils.scores(bid, cap, dfAnnotation1, dfAnnotation_Gold, form.comparison_1.data)
                accuracy2, precision2, recall2, F1_2 = utils.scores(bid, cap, dfAnnotation2, dfAnnotation_Gold, form.comparison_2.data)

                return render_template('comparison_result.html',
                                       text1=nome1,
                                       text2=nome2, file1=metrics1,
                                       file2=metrics2, relazioni_condivise=relazioni_condivise, relazioni_condivise_gold=relazioni_condivise_gold,
                                       relazioni_opposte=relazioni_opposte, entrambi_utenti=entrambi_utenti,
                                       accuracy1=accuracy1, precision1=precision1, recall1=recall1, F1_1=F1_1,
                                       accuracy2=accuracy2, precision2=precision2, recall2=recall2, F1_2=F1_2)

            return render_template('comparison_result.html', text1 = nome1, text2 = nome2, file1=metrics1, file2=metrics2, relazioni_condivise=relazioni_condivise, relazioni_opposte=relazioni_opposte, entrambi_utenti=entrambi_utenti)
    return render_template('comparison.html', form=form)

@app.route('/comparison/<book>')
@login_required
def get_annotation_comparison(book):
    bid = book.split(",")[0]
    cap = book.split(",")[1]

    annotationList = utils.get_list_annotations(bid,cap)

    return jsonify({'annotation': annotationList})

@app.route('/pre_annotator', methods=['GET','POST'])
@login_required
def pre_annotator():
    form = PreAnnotatorForm()
    cap_lista = Conll.query.all()
    choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + " -- Chapter: " + str(cap.cap))) for cap in cap_lista]
    form.book_cap.choices = choices
    if form.validate_on_submit():
        value = form.book_cap.data.split(",")
        bid = value[0]
        cap = value[1]
        # Gets all the words involveded in the book bid and chapter cap
        words_id = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
        words = [Terminology.query.filter_by(tid=word_id.tid).first().lemma for word_id in words_id]
        conll_obj = Conll.query.filter_by(bid=bid, cap=cap).first()
        conll_processed = conll_obj.conll_processed
        conll = utils.conll_annotation(conll_obj.conll)
        sentences = bookStructure.query.filter_by(bid=bid).all()
        sentences = [x.sentence+1 for x in sentences if x.section.startswith(cap) and x.section != cap]
        conll_processed, sentList, tok_to_concept, concept_to_tok = conll_processor_2.conll_processor(conll_processed, 'PROVA', sentences, words)
        #utils.parse_tokToConcept(conll, words)
        #print(tokToConcept)
        #print(sentList)
        parObj = partialAnnotations.query.filter_by(uid = current_user.uid, bid = bid, cap = cap).first()
        if (parObj):
            return render_template("annotator.html", file = {'bid': bid, 'cap': cap, 'concepts': words, 'conll': conll, 'json': parObj.annotation, 'tagged': conll_processed, 'concepts': words, 'tok_to_concept': tok_to_concept, 'concept_to_tok': concept_to_tok, 'sent': sentList})
        return render_template("annotator.html", file = {'bid': bid, 'cap': cap, 'concepts': words,  'conll': conll, 'tagged': conll_processed, 'concepts': words, 'tok_to_concept': tok_to_concept, 'concept_to_tok': concept_to_tok, 'sent': sentList})

    anns_user = db.session \
        .query(Book.title, Book.bid, Annotations.cap, Annotation_user.uid) \
        .join(Annotations, (Annotations.bid == Book.bid)) \
        .join(Annotation_user, (Annotations.aid == Annotation_user.aid) & (Annotation_user.uid == current_user.uid)) \
        .group_by(Book.bid, Annotations.cap) \
        .order_by(Book.title, Annotations.cap)

    anns_others = db.session \
        .query(Book.title, Book.bid, Annotations.cap, Annotation_user.uid, User.name, User.surname) \
        .join(Annotations, (Annotations.bid == Book.bid)) \
        .join(User, (User.uid == Annotation_user.uid)) \
        .join(Annotation_user, (Annotations.aid == Annotation_user.aid) & (Annotation_user.uid != current_user.uid)) \
        .group_by(Annotation_user.uid, Book.bid, Annotations.cap) \
        .order_by(Book.title, Annotations.cap)

    return render_template('pre_annotator.html', form=form, file={"annotations_user": anns_user, "annotations_others":anns_others})

@app.route('/download_ann/<dati>', methods= ['GET'])
@login_required
def download_ann(dati):
    dati = dati.split(",")

    bid = dati[0]
    cap = dati[1]
    uid = dati[2]

    si = io.StringIO()
    cw = csv.writer(si)


    relations = utils.getRelations(bid,cap,"uid."+uid)
    for r in relations:
        cw.writerow(r)


    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=annotation.csv"
    output.headers["Content-type"] = "text/csv"

    return output

@app.route('/annotation_upload', methods=['POST'])
@login_required
def annotation_upload():
    req = request.get_json()
    delAnnotation = partialAnnotations.query.filter_by(uid=current_user.uid, bid=req["bid"], cap=req["cap"]).first()
    if(delAnnotation):
        db.session.delete(delAnnotation)
    parAnnotation = partialAnnotations(uid=current_user.uid, bid=req["bid"], cap=req["cap"], annotation=req["data"])
    db.session.add(parAnnotation)
    db.session.commit()
    message = "The partial annotation was added to the Database"
    res = make_response(jsonify(message))
    return res

@app.route('/final_annotation_upload', methods=['POST'])
@login_required
def final_annotation_upload():
    req = request.get_json()
    delAnnotation = partialAnnotations.query.filter_by(uid=current_user.uid, bid=req["bid"], cap=req["cap"]).first()
    if(delAnnotation):
        db.session.delete(delAnnotation)
    aidAnnotations = Annotations.query.filter_by(bid=req["bid"], cap=req["cap"]).all()
    for item in aidAnnotations:
        delAnnotationUsr = Annotation_user.query.filter_by(aid=item.aid, uid=current_user.uid).all()
        if (delAnnotationUsr):
            for a in delAnnotationUsr:
                db.session.delete(a)
    print(req["data"])
    utils.upload_Annotation(json.loads(req["data"]), req["bid"], req["cap"], current_user.uid)

    # Annotazione pronta per la revisione
    rev = Revision_status.query.filter_by(bid=req["bid"], cap=req["cap"], uid=current_user.uid).first()

    if rev:
        rev.status="Not started"
    else:
        db.session.add(Revision_status(bid=req["bid"], cap=req["cap"], uid=current_user.uid, status="Not started"))
    db.session.commit()

    message = "The annotation was added to the Database"
    res = make_response(jsonify(message))
    return res


@app.route('/pre_revision', methods=['GET','POST'])
@login_required
def pre_revision():
    form = RevisionForm()



    '''
    Versione precedente in cui le relazioni revisionabili erano solo quelle uniche    
    
    # Prendo tutte le annotazioni e il relativo utente e stato
    annotazioni = db.session \
        .query(Book.bid, Conll.cap, Book.title, Annotation_user.uid, Revision_status.status ) \
        .join(Conll, (Conll.bid == Book.bid))\
        .join(Annotations, (Annotations.bid == Book.bid) &(Conll.cap == Annotations.cap) ) \
        .join(Annotation_user, (Annotations.aid == Annotation_user.aid)) \
        .join(Revision_status, (Revision_status.bid == Book.bid) &(Conll.cap == Revision_status.cap) & (Annotation_user.uid == Revision_status.uid))\
        .group_by(Book.bid, Conll.cap, Annotation_user.uid) \
        .order_by(Book.title, Conll.cap) \
        .all()

    # è possibile revisionare solo le annotazioni fatte dall'utente corrente
    # solo se almeno un altro utente ha eseguito l'annotazione di quel libro
    ann_revisionabili = []

    # a[0] -> book id, 1 -> cap, -> 2 title, 3 -> utente, 4 -> stato
    for a in annotazioni:
        if a[3] == current_user.uid:
            for b in annotazioni:
                if a != b and b[0] == a[0] and b[1] == a[1]:
                    if a not in ann_revisionabili:
                        ann_revisionabili.append(a)
    '''

    # Prendo tutte le annotazioni dell'utente
    ann_revisionabili = db.session \
        .query(Book.bid, Conll.cap, Book.title, Annotation_user.uid, Revision_status.status) \
        .join(Conll, (Conll.bid == Book.bid)) \
        .join(Annotations, (Annotations.bid == Book.bid) & (Conll.cap == Annotations.cap)) \
        .join(Annotation_user, (Annotations.aid == Annotation_user.aid) & (Annotation_user.uid == current_user.uid)) \
        .join(Revision_status, (Revision_status.bid == Book.bid) & (Conll.cap == Revision_status.cap) & (
                Annotation_user.uid == Revision_status.uid)) \
        .group_by(Book.bid, Conll.cap, Annotation_user.uid) \
        .order_by(Book.title, Conll.cap) \
        .all()

    form.book_cap.choices = [(str(str(b[0]) + ',' + str(b[1])),
                              ("Title: " + b[2] + " -- Chapter: " + str(b[1]) ))#+ " -- Status: "+ b[4]
                                for b in ann_revisionabili]

    if form.validate_on_submit():

        confirm_tags = ['Lexical relation', 'Functional Relation', 'Definition', 'Example', 'In depth','Causal Relation']
        delete_tags = ["Background knowledge", "Too far", "Annotation error", "Co-requisites", "Wrong direction"]
        weight_tags = ["Weak", "Strong"]

        #inizializzo db
        if not Revision_type.query.filter_by(rev_id=0).first():
            db.session.add(Revision_type(rev_id=0, type='Confirm'))
            db.session.add(Revision_type(rev_id=1, type='Delete'))
            db.session.add(Revision_type(rev_id=2, type='Change weight'))

            for id, tag in enumerate(confirm_tags):
                print(id, tag)
                db.session.add(Revision_tag(tag_id=id, name=tag, rev_id=0))

            for id, tag in enumerate(delete_tags):
                db.session.add(Revision_tag(tag_id=id+len(confirm_tags), name=tag, rev_id=1))

            for id, tag in enumerate(weight_tags):
                db.session.add(Revision_tag(tag_id=id+len(confirm_tags)+len(delete_tags), name=tag, rev_id=2))

            db.session.commit()

        ann_to_review = form.book_cap.data.split(',')
        bid = ann_to_review[0]
        cap = ann_to_review[1]

        # testo
        sentences = bookStructure.query.filter_by(bid=bid).all()
        titles = [x.sentence for x in sentences if x.section.startswith(cap)]

        conll_obj = Conll.query.filter_by(bid=bid, cap=cap).first()
        conll_processed = conll_obj.conll_processed
        conll_processed = conll_processor_2.conll_processor_for_revision(conll_processed,titles)
        

        # relazioni

        AllUsersExceptThis = db.session \
            .query(Annotations.aid,Annotations.lemma1, Annotations.lemma2, Annotation_user.ann_type) \
            .join(Annotation_user, (Annotations.aid == Annotation_user.aid)) \
            .filter(Annotations.bid==bid, Annotations.cap==cap, Annotation_user.uid != current_user.uid)\
            .all()

        ThisUser = db.session \
            .query(Annotations.aid, Annotations.lemma1, Annotations.lemma2,Annotation_user.ann_type, Annotation_user.ann_user_id) \
            .join(Annotation_user, (Annotations.aid == Annotation_user.aid)) \
            .filter(Annotations.bid == bid, Annotations.cap == cap, Annotation_user.uid == current_user.uid) \
            .all()

        # relazioni uniche: solo questo utente le ha messe e nessun'altro utente
        all_rels = []

        for rel in ThisUser:
            # Concetti

            #se un concetto non è un id (intero) vuol dire che è una parola aggiunta manualmente durante l'annotazione ed è già una stringa
            if isinstance(rel[1], int):
                target = Terminology.query.filter_by(tid=int(rel[1])).first().lemma
            else:
                target = rel[1]

            if isinstance(rel[2], int):
                prereq = Terminology.query.filter_by(tid=int(rel[2])).first().lemma
            else:
                prereq = rel[2]

            # ID frase
            id_phrase = Annotations.query.filter_by(aid=int(rel[0])).first().id_phrase

            # guardo se questa relazione è gia stata revisionata
            revised = Revised_annotations.query.filter_by(ann_user_id=rel[4]).first()

            #se è già stata revisionata devo mostrarla con il relativo tag se presente
            if revised:
                revised_value = Revision_type.query.filter_by(rev_id= revised.rev_id).first().type
                tag_id =  revised.tag_id

                if tag_id is not None:
                    tag_value = Revision_tag.query.filter_by(tag_id= tag_id).first().name
                else:
                    tag_value = 'None'
            else:
                revised_value = 'None'
                tag_value = 'None'

            if (rel[0],rel[1],rel[2], rel[3]) not in AllUsersExceptThis:
                item = {"id":rel[4], "target": target, "prereq":prereq, "weight": rel[3], "is_unique":True, "phrase": id_phrase,"revised_value":revised_value, "tag_value":tag_value}
            else:
                item = {"id": rel[4], "target": target, "prereq": prereq, "weight": rel[3], "is_unique": False, "phrase": id_phrase, "revised_value": revised_value, "tag_value": tag_value}

            #if item not in all_rels:
            all_rels.append(item)



        options = ["Confirm","Delete","Change weight"]
        print(confirm_tags)

        return render_template('revision.html', file = {'text':conll_processed, "bid":bid, "cap":cap, 'rels':all_rels, "options":options, "confirm_tags":confirm_tags, "delete_tags":delete_tags})

    return render_template('pre_revision.html', form=form)

#fetch in revision.js
@app.route('/revision_upload', methods=['POST'])
@login_required
def revision_upload():
    try:
        req = request.get_json()
        data = json.loads(req["data"])

        revisione_completata = True

        for r in data:
            if r["rev"] != 'None':
                rev_id = Revision_type.query.filter_by(type=r["rev"]).first().rev_id

                revised = Revised_annotations.query.filter_by(ann_user_id=int(r["ann_user_id"])).first()

                #se non ho già fatto questa revisione la aggiungo
                if not revised:
                    if r['tag'] != 'None':
                        tag_id = Revision_tag.query.filter_by(name= r['tag']).first().tag_id
                        db.session.add(Revised_annotations(ann_user_id=int(r["ann_user_id"]), rev_id=rev_id, tag_id=tag_id))
                    else:
                        db.session.add(Revised_annotations(ann_user_id=int(r["ann_user_id"]), rev_id=rev_id))

                #altrimenti la aggiorno
                else:
                    revised.rev_id = rev_id
                    if r['tag'] != 'None':
                        tag_id = Revision_tag.query.filter_by(name=r['tag']).first().tag_id
                        revised.tag_id = tag_id
                    else:
                        revised.tag_id = None

            #se è presente (almeno) una revisione 'none' vuol dire che la revisione non è finita
            '''elif revisione_completata:
                revisione_completata = False'''

        ''' versione precedete, bisognava finire tutta la revisione per salvare nel db'''
        #aggiorno stato della revisione (revisione finita o non finita)
        status = Revision_status.query.filter_by(bid=req["bid"], cap=req["cap"], uid=current_user.uid).first()
        '''if not revisione_completata:
            if status:
                status.status = "Not finished"
            else:
                db.session.add(Revision_status(bid=req["bid"], cap=req["cap"], uid=current_user.uid, status="Not finished"))
            message = "not finished"
        else:'''
        if status:
            status.status = "Finished"
        else:
            db.session.add(Revision_status(bid=req["bid"], cap=req["cap"], uid=current_user.uid, status="Finished"))
        message = "succeeded"

        db.session.commit()

        res = make_response(jsonify(message))
    except:
        print("error revision:", sys.exc_info())
        message = "fail"
        res = make_response(jsonify(message))

    return res

@app.route('/revision')
@login_required
def revision():
    return render_template("revision.html")

@app.route('/annotator')
@login_required
def annotator():
    return render_template("annotator.html")


@app.route('/matrix')
@login_required
def matrix():
    return render_template("matrix.html")

@app.route('/comparison_result')
@login_required 
def comparison_result():
    return render_template("comparison_result.html")
    

@app.route('/arc_diagram')
@login_required
def arc_diagram():
    return render_template("arc_diagram.html")

@app.route('/simple_graph')
@login_required
def simple_graph():
    return render_template("simple_graph.html")

@app.route('/bezier_graph')
@login_required
def bezier_graph():
    return render_template("bezier_graph.html")

@app.route('/simple_graph_annotator')
@login_required
def simple_graph_annotator():
    return render_template("simple_graph_annotator.html")

@app.route('/bezier_graph_annotator')
@login_required
def bezier_graph_annotator():
    return render_template("bezier_graph_annotator.html")

@app.route('/gantt')
@login_required
def gantt():
    return render_template("gantt.html")


@app.route('/pre_visualization', methods=['GET','POST'])
@login_required
def pre_visualization():
    form = PreVisualizationForm()
    cap_lista = Conll.query.all()
    form.book_cap.choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + " -- Chapter: " + str(cap.cap))) for cap in cap_lista]
    if cap_lista:
        choices = utils.get_list_annotations(cap_lista[0].bid, cap_lista[0].cap)

        for c in choices:
            form.author.choices.append((c['id'], c['name']))


        if form.validate_on_submit():
            value = form.book_cap.data.split(",")
            libro = Book.query.filter_by(bid=value[0]).first()
            nomelibro = libro.title
            bid = value[0]
            cap = value[1]
            words_tid = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
            words = [Terminology.query.filter_by(tid=word.tid).first().lemma for word in words_tid]
            sentences = bookStructure.query.filter_by(bid=bid).all()
            sentences = [sentence for sentence in sentences if str(sentence.section).startswith(str(cap) + ".")]
            conll_obj = Conll.query.filter_by(bid=bid, cap=cap).first()
            conll = conll_obj.conll
            conll_processed = conll_obj.conll_processed

            if form.visualization_type.data == "1":
                if("gold" in str(form.author.data)):
                    dfAnnotation, df, metrics, words = utils.create_dfAnnotation(bid, cap, form.author.data, conll, words)
                    metrics = utils.process_for_matrix_gold(dfAnnotation, df, form.author.data, words,nomelibro)
                    return render_template('matrix_for_gold.html', file=metrics)

                else:
                    dfAnnotation, df, metrics, words = utils.data_analysis(conll, words, sentences, bid, cap, form.author.data)
                    metrics = utils.process_for_matrix(dfAnnotation, df, form.author.data, words, nomelibro)

                if  form.author.data in ["3","5","6"]:
                    return render_template('matrix_baseline.html', file=metrics)
                else:
                    return render_template('matrix.html', file=metrics)
            elif form.visualization_type.data == "2":
                if("gold" in str(form.author.data)):
                    dfAnnotation, df, metrics, words = utils.create_dfAnnotation(bid, cap, form.author.data, conll, words)
                    metrics = utils.process_for_matrix_gold(dfAnnotation, df, form.author.data, words,nomelibro)
                else:
                    dfAnnotation, df, metrics, words = utils.data_analysis(conll, words, sentences, bid, cap, form.author.data)
                    metrics = utils.process_for_matrix(dfAnnotation, df, form.author.data, words,nomelibro)
                return render_template('arc_diagram.html', file=metrics)
            elif form.visualization_type.data == "3":

               if("gold" in str(form.author.data)):
                    dfAnnotation, df, metrics, words = utils.create_dfAnnotation(bid, cap, form.author.data, conll, words)
                    metrics = utils.process_for_matrix_gold(dfAnnotation, df, form.author.data, words,nomelibro)
                    return render_template('choose_graph.html', file=metrics)
               else:
                    dfAnnotation, df, metrics, words = utils.data_analysis(conll, words, sentences, bid, cap, form.author.data)
                    metrics = utils.process_for_matrix(dfAnnotation, df, form.author.data, words, nomelibro)
                    return render_template('choose_graph_annotator.html', file=metrics)


            elif form.visualization_type.data == "4":

                dfAnnotation, df, metrics, words = utils.data_analysis(conll, words, sentences, bid, cap, form.author.data)
                metrics = utils.process_for_matrix(dfAnnotation, df, form.author.data, words,nomelibro)


                titles_id = [x.sentence+1 for x in sentences if x.section.startswith(cap) and x.section != cap]

                #conll_processed, sentList, tok_to_concept, concept_to_tok = conll_processor_2.conll_processor(conll_processed, 'PROVA', titles_id, words)
                sentList = conll_processor_2.sentList(conll_processed,titles_id)

                bursts = []
                bursts_results = Burst_results.query.filter_by(bid=bid, cap=cap).all()

                for burst in bursts_results:
                    bursts.append({'startSent': burst.start+1,'endSent':burst.end+1,'concept': burst.lemma, 'ID': burst.burst_id,
                                   'freqOfTerm': burst.freq,'status': burst.status})

                burstsPair = []
                bursts_rels = Burst_rel_allen.query.filter_by(bid=bid, cap=cap).all()

                for rel in bursts_rels:
                    x =  Burst_results.query.filter_by(burst_id=rel.burst1, bid=bid, cap=cap).first().lemma
                    y = Burst_results.query.filter_by(burst_id=rel.burst2, bid=bid, cap=cap).first().lemma

                    Bx_start = Burst_results.query.filter_by(burst_id=rel.burst1, bid=bid, cap=cap).first().start
                    By_start = Burst_results.query.filter_by(burst_id=rel.burst2, bid=bid, cap=cap).first().start
                    Bx_end = Burst_results.query.filter_by(burst_id=rel.burst1, bid=bid, cap=cap).first().end
                    By_end = Burst_results.query.filter_by(burst_id=rel.burst2, bid=bid, cap=cap).first().end

                    burstsPair.append({'x':x, 'y': y, 'Bx_id': rel.burst1, 'By_id': rel.burst2, 'Bx_start': Bx_start+1,
                                       'Bx_end': Bx_end+1, 'By_start': By_start+1, 'By_end': By_end+1, 'Rel': rel.type})


                return render_template('gantt.html', bid=bid, cap=cap, bursts=bursts, burstsPair=burstsPair, words=words, file=metrics, sentList=sentList)
    return render_template('pre_visualization.html', form=form)

@app.route('/get_json_grafo/<data>', methods=['GET','POST'])
@login_required
def get_json_data(data):
    print(data)
    value = data.split(",")
    libro = Book.query.filter_by(bid=value[0]).first()
    nomelibro = libro.title
    bid = value[0]
    cap = value[1]
    author = value[2]
    words_tid = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
    words = [Terminology.query.filter_by(tid=word.tid).first().lemma for word in words_tid]
    sentences = bookStructure.query.filter_by(bid=bid).all()
    sentences = [sentence for sentence in sentences if str(sentence.section).startswith(str(cap) + ".")]
    conll_obj = Conll.query.filter_by(bid=bid, cap=cap).first()
    conll = conll_obj.conll
    if ("gold" in str(author)):
        dfAnnotation, df, metrics, words = utils.create_dfAnnotation(bid, cap, author, conll, words)
        metrics = utils.process_for_matrix_gold(dfAnnotation, df, author, words, nomelibro)
    else:
        dfAnnotation, df, metrics, words = utils.data_analysis(conll, words, sentences, bid, cap, author)
        metrics = utils.process_for_matrix(dfAnnotation, df, author, words, nomelibro)


    return jsonify({'file': metrics})

@app.route('/download_gantt/<dati>', methods= ['GET'])
@login_required
def download_gantt(dati):
    dati = dati.split(",")

    bid = dati[0]
    cap = dati[1]

    bursts_results = Burst_results.query.filter_by(bid=bid, cap=cap).all()

    si = io.StringIO()
    cw = csv.writer(si)

    cw.writerow(["ID", "Start sent", "End sent", "Lemma", "Frequency", "Status"])

    for burst in bursts_results:

        cw.writerow([burst.burst_id, burst.start + 1, burst.end + 1, burst.lemma, burst.freq, burst.status])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=bursts.csv"
    output.headers["Content-type"] = "text/csv"

    return output

@app.route('/visualization/<book>')
@login_required
def get_authors(book):
    bid = book.split(",")[0]
    cap = book.split(",")[1]

    annotationList = utils.get_list_annotations(bid, cap)

    return jsonify({'annotation': annotationList})

@app.route('/linguistic_analysis')
@login_required
def linguistic_analysis():
    return render_template("linguistic_analysis.html")

@app.route('/data_summary')
@login_required
def data_summary():
    return render_template("data_summary.html")

@app.route('/agreement')
@login_required
def agreement():
    return render_template("agreement.html")

@app.route('/visualization')
@login_required
def visualization():
    return render_template("visualization.html")  

@app.route('/gold_standard', methods=['GET','POST'])
@login_required
def gold_standard():
    form = GoldStandardForm()

    cap_lista = Conll.query.all()
    form.book_cap.choices = [(str(str(cap.bid) + ',' + str(cap.cap)), ("Title: " + (db.session.query(Book.title).join(Conll, cap.bid == Book.bid).first()).title + " -- Chapter: " + str(cap.cap))) for cap in cap_lista]


    annotation_choices = []

    if cap_lista:
        user_list = []
        #form.author.choices = []
        annotations = Annotations.query.filter_by(cap = cap_lista[0].cap, bid = cap_lista[0].bid).all()
        for relationship in annotations:
            users_annotations = Annotation_user.query.filter_by(aid = relationship.aid).all()
            for poss_user in users_annotations:
                if poss_user.uid not in user_list:
                    user_list.append(poss_user.uid)
                    user = User.query.filter_by(uid = poss_user.uid).first()
                    annotation_choices.append(("uid." + str(user.uid), "Annotation of: " + str(user.name) + " " + str(user.surname)))

    form.annotation.choices = annotation_choices

    if form.validate_on_submit():
            value = form.book_cap.data.split(",")
            bid = value[0]
            cap = value[1]
            agreement = request.form.get('agreements')
            gold_name = form.name.data

            if agreement == "UNION":
                agreement = "0%"
            elif agreement == "INTERSECTION":
                agreement = "100%"


            words_tid = Terminology_reference.query.filter_by(bid=bid, cap=cap).all()
            sentences = bookStructure.query.filter_by(bid=bid).all()
            sentences = [sentence for sentence in sentences if str(sentence.section).startswith(str(cap) + ".")]
            conll = Conll.query.filter_by(bid=bid, cap=cap).first().conll
            words = [Terminology.query.filter_by(tid=word.tid).first().lemma for word in words_tid]

            uids = form.annotation.data


            df = utils.create_gold(uids, bid, cap, words, conll, sentences,agreement)
            uids_lista = ""
            for uid in uids:
                uids_lista += uid + " "

            gold_standard = goldStandard.query.filter_by(bid=bid, cap=cap).first()

            if not gold_standard:
                goldStd = goldStandard(bid=bid, cap=cap, uids=uids_lista, name=gold_name, gold=df, agreements=agreement)
                db.session.add(goldStd)
            else:
                gold_standard.uids = uids_lista
                gold_standard.agreements = agreement
                gold_standard.gold = df
                gold_standard.name = gold_name

            db.session.commit()
            flash("The gold has been created!", "success")


            golds = db.session \
                .query(Book.title, goldStandard.bid, goldStandard.cap, goldStandard.name) \
                .filter(Book.bid == goldStandard.bid) \
                .order_by(Book.title)
            return render_template('gold_standard.html', form=form, file={"golds":golds})


    golds = db.session \
        .query(Book.title, goldStandard.bid, goldStandard.cap, goldStandard.name) \
        .filter(Book.bid == goldStandard.bid) \
        .order_by(Book.title)
    return render_template('gold_standard.html', form=form, file={"golds":golds})


@app.route('/download_gold/<dati>', methods= ['GET'])
@login_required
def download_gold(dati):
    dati = dati.split(",")

    bid = dati[0]
    cap = dati[1]

    si = io.StringIO()
    cw = csv.writer(si)


    relations = utils.get_df_gold(goldStandard.query.filter_by(bid=bid, cap=cap).first().gid)
    for r in relations.itertuples():
        cw.writerow([r.prerequisites, r.subsidiaries])


    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=gold.csv"
    output.headers["Content-type"] = "text/csv"

    return output


@app.route('/gold_standard/<book>')
@login_required
def get_annotations(book):
    bid = book.split(",")[0]
    cap = book.split(",")[1]
    annotationList = []
    #Get users annotation
    annotationRel = Annotations.query.filter_by(cap = cap, bid = bid).all()
    users = []
    for annotations in annotationRel:
        annotationUsr = Annotation_user.query.filter_by(aid = annotations.aid).all()
        for userz in annotationUsr:
            if userz and userz.uid not in users:
                    users.append(userz.uid)
                    annotationObj = {}
                    annotationObj["id"] = "uid." + str(userz.uid)
                    annotationObj["name"] = "Annotation of: " + str(User.query.filter_by(uid=userz.uid).first().name) + " " + str(User.query.filter_by(uid=userz.uid).first().surname)
                    annotationList.append(annotationObj)

        
    return jsonify({'annotation': annotationList})

@app.route('/gold_standard2/<agreements>', methods=['GET','POST'])
@login_required
def get_agreements(agreements):
    agreementsList = []
    ann = int(agreements)
    for i in range(ann):
          #print(i)
          tot = (i/(ann-1))
          percentage = "{:.0%}".format(tot)
          #print(percentage)
          if percentage == "0%":
              percentage = "UNION"
          elif percentage == "100%":
              percentage = "INTERSECTION"

          agreementsList.append(str(percentage))

    #print(agreementsList)
    return jsonify({'agreements': agreementsList})

@app.route('/guidelines')
@login_required
def guidelines():
    return render_template("guidelines.html")

@app.route('/methods_description')
@login_required
def methods_description():
    return render_template("methods_description.html")

@app.route('/revision_description')
@login_required
def revision_description():
    return render_template("revision_description.html")

@app.route('/visualization_description')
@login_required
def visualization_description():
    return render_template("visualization_description.html")
    

@app.route('/text_upload', methods=['GET'])
@login_required
def text_upload():
    return render_template('text_upload.html')

@app.route("/text_upload", methods=['POST'])
def email_process():
    
    req = request.get_json()
    book = Book.query.filter_by(title=req["book"], year=req["year"]).first()
    if book:
        
        book_structure = bookStructure.query.filter_by(bid=book.bid, section=req["cap"]).first()
        if book_structure:
            message = "This chapter was already in the Database"
            res = make_response(jsonify(message))
            return res
    
    
    conll = utils.conll_gen(req["text"])
    idPhrase = utils.id_phrase(conll, req["result"])

    # Risolvo bug degli span
    toRemove = []

    if (len(idPhrase) != len(req["result"])):
        for index, t in enumerate(req['result']):
            if t.startswith('<span>'):
                toRemove.append(index)

    for i in toRemove:
        req["result"].pop(i)

    
    
    if(len(idPhrase) == len(req["result"])):
        
        
        # check if someone already register the book
        book = Book.query.filter_by(title=req["book"], year=req["year"]).first()
        if not book:
            # Add book to database
            print(req)
            book = Book(title=req["book"], year=req["year"], category=req["category"], language=req["language"])
            db.session.add(book)
            db.session.commit()
            
            # Add authors to database
            authors = req["author"].split(",")
            for name in authors:
                author = Author(name=name, books=book)
                db.session.add(author)
                db.session.commit()
        else:
            # the email exists
            pass
        
        book_structure = bookStructure.query.filter_by(bid=book.bid, section=req["cap"]).first()
        if not book_structure:
            # Add structure to database
            book_structure = bookStructure(bid=book.bid, section=req["cap"], uid = current_user.uid, sentence = 1)
            db.session.add(book_structure)
            db.session.commit()
        
            for i, phrase in enumerate(req["result"]):
                curr_section = re.search(r'(\d*\.\d*)*', phrase).group()
                book_structure = bookStructure(bid=book.bid, section=curr_section, sentence = str(idPhrase[i]), loader = current_user)
                db.session.add(book_structure)
                db.session.commit()
        
        # get the processed conll
            conll_processed = utils.processConll(conll, book.bid)
    
        # Add connl to database
            conll = Conll(bid=book.bid, cap=req["cap"], conll=conll, conll_processed=conll_processed)       
            db.session.add(conll)
            db.session.commit() 
        
        else:
            # The book cap is already in the DB 
            message = "This chapter was already in the Database"
            res = make_response(jsonify(message))
            return res

        # Inizializzo gli stati dei bs a not ready e lo stato della terminologia a ready (da caricare)
        for i in range(1,7):
            stato = Bs_status(bid=book.bid, cap=req["cap"], method=i, status="not ready")
            db.session.add(stato)

        statoTerm = Terminology_status(bid=book.bid, cap=req["cap"], status="ready")
        db.session.add(statoTerm)

        db.session.commit()
    
        message = "The chapter and the annotation was added to the Database"
        res = make_response(jsonify(message))
        return res
    else:
        print(idPhrase)
        print(len(idPhrase))
        print(req['result'])
        print(len(req["result"]))
        message = "There was a problem with the chapter identification"
        res = make_response(jsonify(message))
        return res
    #     if (request.method == 'POST'):
#        data = request.form
##       data = data["book"]
       
#        return render_template("result.html",result = data)

def load(method):
    global th
    global finished
    finished = False
    th = Thread(method, args=())
    th.start()
    flash("Baseline method completed", "success")
    return render_template('index.html')



@app.route('/result')
def result():
    """ Just give back the result of your heavy work """
    return 'Done'


@app.route('/status')
def thread_status():
    """ Return the status of the worker thread """
    return jsonify(dict(status=('finished' if finished else 'running')))
