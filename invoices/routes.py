from flask import Blueprint, render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user

from extensions import db
from models import Invoice
from invoices.forms import InvoiceForm
from pdf_service import generate_invoice_pdf

invoices_bp = Blueprint("invoices", __name__, template_folder="../templates/invoices")


def _calc(invoice):
    tax_amount = round((invoice.amount or 0) * (invoice.tax or 0) / 100, 2)
    total = round((invoice.amount or 0) + tax_amount, 2)
    return {"tax_amount": tax_amount, "total": total}


def _form_to_data(form):
    return {
        "client_name": form.client_name.data.strip(),
        "client_email": form.client_email.data.strip() if form.client_email.data else None,
        "project_details": form.project_details.data.strip(),
        "services": form.services.data.strip(),
        "amount": form.amount.data,
        "tax": form.tax_percent.data or 0,
        "due_date": form.due_date.data,
    }


@invoices_bp.route("/")
@login_required
def list_invoices():
    invoices = (
        Invoice.query.filter_by(user_id=current_user.id)
        .order_by(Invoice.created_at.desc())
        .all()
    )
    return render_template("invoices/list.html", invoices=invoices)


@invoices_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_invoice():
    form = InvoiceForm()
    if form.validate_on_submit():
        data = _form_to_data(form)
        invoice = Invoice(user_id=current_user.id, **data)
        db.session.add(invoice)
        db.session.flush()  # get invoice.id before commit
        invoice.invoice_number = f"INV-{invoice.id:05d}"
        db.session.commit()

        flash("Invoice created successfully.", "success")
        return redirect(url_for("invoices.view_invoice", invoice_id=invoice.id))

    return render_template("invoices/form.html", form=form, mode="new")


@invoices_bp.route("/<int:invoice_id>")
@login_required
def view_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    return render_template("invoices/view.html", invoice=invoice, calc=_calc(invoice))


@invoices_bp.route("/<int:invoice_id>/edit", methods=["GET", "POST"])
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    form = InvoiceForm(obj=invoice, tax_percent=invoice.tax)

    if form.validate_on_submit():
        data = _form_to_data(form)
        for key, value in data.items():
            setattr(invoice, key, value)
        db.session.commit()
        flash("Invoice updated.", "success")
        return redirect(url_for("invoices.view_invoice", invoice_id=invoice.id))

    return render_template("invoices/form.html", form=form, mode="edit", invoice=invoice)


@invoices_bp.route("/<int:invoice_id>/delete", methods=["POST"])
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    db.session.delete(invoice)
    db.session.commit()
    flash("Invoice deleted.", "info")
    return redirect(url_for("invoices.list_invoices"))


@invoices_bp.route("/<int:invoice_id>/pdf")
@login_required
def download_pdf(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    buffer = generate_invoice_pdf(invoice)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{invoice.invoice_number or ('invoice_' + str(invoice.id))}.pdf",
    )
