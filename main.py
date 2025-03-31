import secrets
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os
import bcrypt
# from Python.sendHtmlEmail import SendHTMLEmail
from Python.sendEmail import sendSimpleEmail, codeGenerate

app = Flask(__name__)

# Load Environment Variables
load_dotenv()
# Connection to MySQL
app.config["MYSQL_USER"] = os.getenv("MY_DB_USER") 
app.config["MYSQL_PASSWORD"] = os.getenv("MY_DB_PW")
app.config["MYSQL_DB"] = os.getenv("MY_DB")

mysql = MySQL(app)

#Creación de contraseña secreta para las sesiones
app.secret_key = secrets.token_urlsafe(32)

weekDays = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
# Index (Login) Route
@app.route('/', methods=['GET', 'POST'])
def index():
    session.pop("ResUser", None)
    session.pop("CodeForPw", None)
    if request.method == "POST":
        userName = request.form["User"]
        Password = request.form["Pass"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT ID_User, Password, NameUser FROM users WHERE NameUser = %s", (userName,))
        sqlValue = cur.fetchone()
        cur.close()

        if sqlValue is not None:
            isChecked = bcrypt.checkpw(Password.encode('utf-8'), sqlValue[1].encode('utf-8'))

            if isChecked:
                session["ID_User"] = sqlValue[0]
                session["User_Name"] = sqlValue[2]
                return redirect(url_for("productsSection"))
            else:
                flash("El usuario y/o la contraseña son incorrectos.", "error")
                return redirect(url_for("index"))
        else:
            flash("No existe este usuario.", "error")
            return redirect(url_for("index"))

    return render_template("index.html")

# Logout Route
@app.route('/logout', methods=['GET'])
def logout():
    session.pop("ID_User", None)
    session.pop("ResUser", None)
    session.pop("CodeForPw", None)
    session.pop("User_Name", None)
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("index"))

# Password Recovery Route
@app.route('/passwordRecovery', methods=['GET', 'POST'])
def passwordRecovery():
    session.pop("ResUser", None)
    session.pop("CodeForPw", None)

    if request.method == "POST":
        emailUser = request.form["Email"].lower()

        cur = mysql.connection.cursor()
        cur.execute("SELECT NameUser FROM users WHERE Email = %s", (emailUser,))
        sqlValue = cur.fetchone()
        cur.close()

        if sqlValue is not None:
            codeSixDigits = codeGenerate()
            sendEmail=sendSimpleEmail(os.getenv("MY_EMAIL"), emailUser, "Abarrotes Patch \nHola, tu código de recuperación para restablecer su contraseña es: " + codeSixDigits, "Código para restablecer su Contraseña")

            if sendEmail != False:
                session["CodeForPw"] = codeSixDigits
                print(codeSixDigits)
                session['ResUser'] = sqlValue[0]
                return redirect(url_for("passwordUpdate"))
            else:
                flash("No se pudo enviar el correo electrónico.", "error")
                return redirect(url_for("passwordRecovery"))

        else:
            flash("No existe un usuario con este correo en el sistema.", "error")
            return redirect(url_for("passwordRecovery"))

    return render_template("passwordRecovery.html")

# Password Update Route
@app.route('/passwordUpdate', methods=['GET', 'POST'])
def passwordUpdate():
    try:
        if 'ResUser' in session:
            if request.method == "POST":
                Code = request.form["Code"].upper()
                newPassword = request.form["Pass"]

                if Code == session["CodeForPw"]:
                    newPassword = newPassword.encode('utf-8')
                    salt = bcrypt.gensalt(12)
                    hashPassword = bcrypt.hashpw(newPassword, salt)
                    cur = mysql.connection.cursor()
                    cur.execute("UPDATE users SET Password = %s WHERE NameUser = %s", (hashPassword, session.get("ResUser")))
                    mysql.connection.commit()
                    cur.close()
                    session.pop("ResUser", None)
                    session.pop("CodeForPw", None)
                    flash("Contraseña actualizada correctamente.", "success")
                    return redirect(url_for("index"))
                else:
                    flash("El código ingresado es incorrecto.", "error")
                    return redirect(url_for("passwordUpdate"))
        else:
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

    return render_template("updatePassword.html")

# Products Route
@app.route('/productsSection', methods=['GET'])
def productsSection():
    try:
        if 'ID_User' in session:
            if request.method == "GET":
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM products")
                sqlValue = cur.fetchall()
                cur.close()
                return render_template("productsSection.html", allProducts=sqlValue)
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))
    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")


# Add Product Route
@app.route('/addProduct', methods=['GET', 'POST'])
def addProduct():
    try:
        if 'ID_User' in session:

            if request.method == 'POST':
                idProduct = int (request.form["ID"])
                name = request.form["Nombre"]
                cost = float(request.form["Costo"])
                price = float(request.form["Precio"])
                # stock = int(request.form["Cantidad"])
                date = request.form["Fecha"]
                description = request.form["Descripcion"]
                cur = mysql.connection.cursor()
                cur.execute("SELECT ID_Product FROM products WHERE ID_Product = %s OR Name = %s", (idProduct, name))
                sqlValue = cur.fetchone()

                if sqlValue is None: # Si no existe un producto con ese ID o nombre lo agrega
                    if date == '':
                        cur.execute("INSERT INTO products (ID_Product, Name, Cost, Price, Quantity, Description) VALUES (%s, %s, %s, %s, 0, %s)", (idProduct, name, cost, price, description))
                    else:
                        cur.execute("INSERT INTO products (ID_Product, Name, Cost, Price, Quantity, Expiration_Date, Description) VALUES (%s, %s, %s, %s, 0, %s, %s)", (idProduct, name, cost, price, date, description))
                    mysql.connection.commit()
                    cur.close()
                    flash(f"Producto {name} agregado correctamente.", "success")
                    return redirect(url_for("addProduct"))

                else:
                    flash("El ID o Nombre del producto ya existe.", "error")

        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
    return render_template("newProductSection.html")

# Delete Product Route
@app.route('/deleteProduct/<int:id>', methods=['GET'])
def deleteProduct(id):
    try:

        if 'ID_User' in session:
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID FROM orders WHERE ID_Product = %s", (id,))
            sqlValue = cur.fetchall()

            if sqlValue == tuple(): # Si no existe una orden con ese ID lo elimina
                cur.execute("DELETE FROM products WHERE ID_Product = %s", (id,))
                mysql.connection.commit()
                cur.close()
                flash("Producto eliminado correctamente.", "success")
                return redirect(url_for("productsSection"))
            else:
                cur.close()
                sqlValue = [str(i[0]) for i in sqlValue]
                sqlValue = ', '.join(sqlValue)
                flash(f"No se puede eliminar el producto ya que tiene compras asociadas. Compra(s) número: {sqlValue}", "error")
                return redirect(url_for("productsSection"))
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

# Update Product Route
@app.route(('/updateProduct/<int:id>'), methods=['GET', 'POST'])
def updateProduct(id):
    try:

        if 'ID_User' in session:
            if request.method == "GET":
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM products WHERE ID_Product = %s", (id,))
                sqlValue = cur.fetchone()
                cur.close()
                return render_template("updateProductSection.html", producto=sqlValue)

            if request.method == "POST":
                idProduct = int (request.form["IDProducto"])
                name = request.form["Nombre"]
                cost = float(request.form["Costo"])
                price = float(request.form["Precio"])
                # stock = int(request.form["Cantidad"])
                date = request.form["Fecha"]
                description = request.form["Descripcion"]
                cur = mysql.connection.cursor()
                cur.execute("SELECT ID_Product FROM products WHERE (ID_Product = %s OR Name = %s) AND ID_Product != %s", (idProduct, name,id))

                sqlValue = cur.fetchone()
                if sqlValue is None: # Si no existe un producto con ese ID o nombre actualiza todo
                    if date == '':
                        cur.execute("UPDATE products SET ID_Product = %s, Name = %s, Cost = %s, Price = %s, Expiration_Date = NULL, Description = %s WHERE ID_Product = %s", (idProduct, name, cost, price, description, id))
                    else:
                        cur.execute("UPDATE products SET ID_Product = %s, Name = %s, Cost = %s, Price = %s, Expiration_Date = %s, Description = %s WHERE ID_Product = %s", (idProduct, name, cost, price, date, description, id))
                    flashMessage = "Todos los campos del producto se actualizaron correctamente."
                    id = idProduct

                else:
                    if date == '':
                        cur.execute("UPDATE products SET Cost = %s, Price = %s, Expiration_Date = NULL, Description = %s WHERE ID_Product = %s", (cost, price, description, id))
                    else:
                        cur.execute("UPDATE products SET Cost = %s, Price = %s, Expiration_Date = %s, Description = %s WHERE ID_Product = %s", (cost, price, date, description, id))
                    flashMessage = "No se actualizo el ID o Nombre por que ya existen."

                    if idProduct != sqlValue[0]:
                        id = idProduct

                mysql.connection.commit()
                cur.close()
                flash(flashMessage, "success")
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))
        
    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

    return redirect(url_for("updateProduct", id=id))

# User Profile Route
@app.route('/userProfile', methods=['GET', 'POST'])
def userProfile():
    try:
        if 'ID_User' in session:
            if request.method == "GET":
                cur = mysql.connection.cursor()
                cur.execute("SELECT ID_User, NameUser, Email FROM users WHERE ID_User = %s", (session["ID_User"],))
                sqlValue = cur.fetchone()
                cur.close()
                return render_template("userProfileSection.html", dataUser=sqlValue)

            if request.method == 'POST':
                name = request.form["Nombre"]
                email = request.form["Correo"]
                cur = mysql.connection.cursor()
                cur.execute("SELECT ID_User FROM users WHERE (NameUser = %s OR Email = %s) AND NameUser!=%s", (name, email, session["User_Name"]))
                sqlValue = cur.fetchone()

                if sqlValue is None: # Si no existe un usuario con ese ID o nombre lo actualiza
                    cur.execute("UPDATE users SET NameUser = %s, Email = %s WHERE ID_User = %s", (name, email, session["ID_User"]))
                    mysql.connection.commit()
                    cur.close()
                    session["User_Name"] = name
                    flash("Usuario actualizado correctamente.", "success")
                else:
                    flash("El Nombre o Correo ya existen.", "success")

        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
    return redirect(url_for("userProfile"))

# Vendors Route
@app.route('/vendorsSection', methods=['GET'])
def vendorsSection():
    try:
        if 'ID_User' in session:
            if request.method == "GET":
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM vendors")
                sqlValue = cur.fetchall()
                cur.close()
                return render_template("vendorsSection.html", allVendors=sqlValue, week = weekDays)
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

# Add Vendor Route
@app.route('/addVendor', methods=['GET', 'POST'])
def addVendor():
    try:
        if 'ID_User' in session:

            if request.method == "POST":
                idVendor = int(request.form["IDVendor"])
                name = request.form["Nombre"]
                number = request.form["Numero"]
                date = request.form["Dia"]
                cur = mysql.connection.cursor()
                cur.execute("SELECT ID_Vendor FROM vendors WHERE ID_Vendor = %s OR Name = %s", (idVendor, name))
                sqlValue = cur.fetchone()

                if sqlValue is None: # Si no existe un producto con ese ID o nombre lo agrega
                    cur.execute("INSERT INTO vendors (ID_Vendor, Name, Number, Visit_Day) VALUES (%s, %s, %s, %s)", (idVendor, name, number, date))
                    mysql.connection.commit()
                    cur.close()
                    flash(f"Proveedor {name} agregado correctamente.", "success")
                    return redirect(url_for("addVendor"))
                else:
                    flash("El ID o Nombre del proveedor ya existe.", "error")
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

    return render_template("newVendorSection.html")

# Delete Vendor Route
@app.route('/deleteVendor/<int:id>', methods=['GET'])
def deleteVendor(id):
    try:

        if 'ID_User' in session:
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID FROM orders WHERE ID_Vendor = %s", (id,))
            sqlValue = cur.fetchall()

            if sqlValue == tuple(): # Si no existe una orden con ese ID lo elimina
                cur.execute("DELETE FROM vendors WHERE ID_Vendor = %s", (id,))
                mysql.connection.commit()
                cur.close()
                flash("Proveedor eliminado correctamente.", "success")
                return redirect(url_for("vendorsSection"))
            else:
                sqlValue = [str(i[0]) for i in sqlValue]
                sqlValue = ', '.join(sqlValue)
                cur.close()
                flash(f"No se puede eliminar el proveedor ya que tiene compras asociadas. Compra(s) número: {sqlValue}.", "error")
                return redirect(url_for("vendorsSection"))
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

# Update Vendor Route
@app.route(('/updateVendor/<int:id>'), methods=['GET', 'POST'])
def updateVendor(id):
    try:

        if 'ID_User' in session:
            if request.method == "GET":
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM vendors WHERE ID_Vendor = %s", (id,))
                sqlValue = cur.fetchone()
                cur.close()
                return render_template("updateVendorSection.html", proveedor=sqlValue)

            if request.method == "POST":
                idVendor = int(request.form["IDVendor"])
                name = request.form["Nombre"]
                Number = request.form["Numero"]
                date = request.form["Dia"]
                cur = mysql.connection.cursor()
                cur.execute("SELECT ID_Vendor FROM vendors WHERE (ID_Vendor = %s OR Name = %s) AND ID_Vendor != %s", (idVendor, name,id))
                sqlValue = cur.fetchone()

                if sqlValue is None: # Si no existe un producto con ese ID o nombre actualiza todo
                    cur.execute("UPDATE vendors SET ID_Vendor = %s, Name = %s, Number = %s, Visit_Day = %s WHERE ID_Vendor = %s", (idVendor, name, Number, date ,id))
                    flashMessage = "Los campos del proveedor fueron actualizados."

                    if idVendor != id:
                        id = idVendor

                else:
                    flashMessage = "No se actualizaron los datos ya que el ID o Nombre ya existen."

                mysql.connection.commit()
                cur.close()
                flash(flashMessage, "success")
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))
    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

    return redirect(url_for("updateVendor", id=id))

# Orders Route
@app.route('/ordersSection', methods=['GET'])
def ordersSection():
    try:
        if 'ID_User' in session:
            if request.method == "GET":
                cur = mysql.connection.cursor()
                cur.execute("SELECT orders.ID, products.Name, vendors.Name, orders.Quantity, orders.Unit_Cost, orders.Cost, orders.Date FROM orders JOIN vendors ON orders.ID_Vendor = vendors.ID_Vendor JOIN products ON orders.ID_Product = products.ID_Product")
                sqlValue = cur.fetchall()
                cur.close()
                return render_template("ordersSection.html", allOrders=sqlValue)
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

# Add Order Route
@app.route('/addOrder', methods=['GET', 'POST'])
def addOrder():
    try:
        if 'ID_User' in session:

            if request.method == "GET":
                cur = mysql.connection.cursor()
                cur.execute("SELECT ID_Vendor, Name FROM vendors")
                sqlValue = cur.fetchall()
                cur.execute("SELECT ID_Product, Name FROM products")
                sqlValue2 = cur.fetchall()
                cur.close()
                return render_template("newOrderSection.html", allIDVendors=sqlValue, allIDProducts=sqlValue2)

            if request.method == "POST":
                idOrder = int(request.form["ID"])
                idVendor = int(request.form["IDVendor"])
                idProduct = int(request.form["IDProduct"])
                unitCost = float(request.form["CostoUnidad"])
                Totalcost = float(request.form["CostoTotal"])
                quantity = int(request.form["Cantidad"])
                date = request.form["Fecha"]
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM orders WHERE ID = %s", (idOrder,))
                sqlValue = cur.fetchone()

                if sqlValue is None: # Si no existe una orden con ese ID lo agrega
                    cur.execute("INSERT INTO orders (ID, ID_Vendor, ID_Product, Quantity, Unit_Cost, Cost, Date) VALUES (%s, %s, %s, %s, %s, %s, %s)", (idOrder, idVendor, idProduct, quantity, unitCost ,Totalcost, date))
                    mysql.connection.commit()
                    cur.execute("UPDATE products SET Quantity = Quantity + %s WHERE ID_Product = %s", (quantity, idProduct))
                    mysql.connection.commit()
                    cur.close()
                    flash(f"Compra Número {idOrder} agregada correctamente.", "success")
                else:
                    flash("Ya existe una compra con esa clave o fecha.", "error")
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

    return redirect(url_for("addOrder"))

# Delete Order Route
@app.route('/deleteOrder/<int:id>', methods=['GET'])
def deleteOrder(id):
    try:

        if 'ID_User' in session:
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID_Product, Quantity FROM orders WHERE ID = %s", (id,))
            sqlValue = cur.fetchone()
            cur.execute("DELETE FROM orders WHERE ID = %s", (id,))
            mysql.connection.commit()
            cur.execute("UPDATE products SET Quantity = Quantity - %s WHERE ID_Product = %s", (sqlValue[1], sqlValue[0]))
            mysql.connection.commit()
            cur.close()
            flash("Compra eliminada correctamente.", "success")
            return redirect(url_for("ordersSection"))
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

@app.route(('/updateOrder/<int:id>'), methods=['GET', 'POST'])
def updateOrder(id):
    try:
        if 'ID_User' in session:
            cur = mysql.connection.cursor()
            # Obtener la orden original
            cur.execute("SELECT * FROM orders WHERE ID = %s", (id,))
            order_original = cur.fetchone()
            if not order_original:
                flash("La orden no existe.", "error")
                return redirect(url_for("ordersSection"))  # O a la vista de órdenes

            if request.method == "GET":
                cur.execute("SELECT ID_Vendor, Name FROM vendors")
                sqlValue2 = cur.fetchall()
                cur.execute("SELECT ID_Product, Name FROM products")
                sqlValue3 = cur.fetchall()
                cur.close()
                return render_template("updateOrderSection.html", compra=order_original, allIDVendors=sqlValue2, allIDProducts=sqlValue3)

            if request.method == "POST":
                idOrder = int(request.form["ID"])  # Posible nuevo ID
                idVendor = int(request.form["IDVendor"])
                idProduct = int(request.form["ID_Product"])
                unitCost = float(request.form["CostoUnidad"])
                Totalcost = float(request.form["CostoTotal"])
                quantity = int(request.form["Cantidad"])
                date = request.form["Fecha"]

                # Si se cambia el ID, verificamos que no exista ya otra orden con ese ID
                if idOrder != id:
                    cur.execute("SELECT * FROM orders WHERE ID = %s", (idOrder,))
                    order_check = cur.fetchone()
                    if order_check:
                        flash("Ya existe una venta con esa clave.", "error")
                        cur.close()
                        return redirect(url_for("updateOrder", id=id))

                cur.execute("UPDATE orders SET ID = %s, ID_Vendor = %s, ID_Product = %s, Quantity = %s, Unit_Cost = %s, Cost = %s, Date = %s WHERE ID = %s", (idOrder, idVendor, idProduct, quantity, unitCost, Totalcost, date, id))
                mysql.connection.commit()
                cur.execute("UPDATE products SET Quantity = Quantity - %s WHERE ID_Product = %s", (order_original[3], order_original[2]))
                mysql.connection.commit()
                cur.execute("UPDATE products SET Quantity = Quantity + %s WHERE ID_Product = %s", (quantity, idProduct))
                mysql.connection.commit()
                cur.close()

                flash(f"Compra número {idOrder} actualizada correctamente.", "success")
                return redirect(url_for("updateOrder", id=idOrder))
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))
    except Exception as error:
        print(error)
        flash(f"Ocurrió un error: {error}.", "error")
        return redirect(url_for("updateOrder", id=id))


# Sales Route
@app.route('/salesSection', methods=['GET'])
def salesSection():
    try:
        if 'ID_User' in session:
            if request.method == "GET":
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM sales")
                sqlValue = cur.fetchall()
                cur.close()
                return render_template("salesSection.html", allSales=sqlValue)
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

# Add Sale Route
@app.route('/addSale', methods=['GET', 'POST'])
def addSale():
    try:
        if 'ID_User' in session:

            if request.method == "POST":
                idSale = request.form["ID"]
                date = request.form["Fecha"]
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM sales WHERE ID_Sale = %s OR Date = %s", (idSale, date))
                sqlValue = cur.fetchone()

                if sqlValue is None: # Si no existe una venta con ese ID y fecha lo agrega
                    cur.execute("INSERT INTO sales (ID_Sale, Date, Active) VALUES (%s, %s,'SI')", (idSale, date))
                    mysql.connection.commit()
                    cur.close()
                    flash(f"Venta número {idSale} agregada correctamente.", "success")
                    return redirect(url_for("addSale"))
                else:
                    flash("Ya existe una venta con esa clave o fecha.", "error")
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

    return render_template("newSaleSection.html")

# Update Sale Route
@app.route('/updateSale/<int:id>', methods=['GET', 'POST'])
def updateSale(id):
    try:
        if 'ID_User' in session:
            if request.method == "GET":
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM sales WHERE ID_Sale = %s", (id,))
                sqlValue = cur.fetchone()
                cur.close()
                return render_template("updateSaleSection.html", venta=sqlValue)

            if request.method == "POST":
                idSale = request.form["ID"]
                date = request.form["Fecha"]
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM sales WHERE (ID_Sale = %s OR Date = %s) AND ID_Sale != %s", (idSale, date, id))
                sqlValue = cur.fetchone()

                if sqlValue is None: # Si no existe una venta con ese ID y fecha lo agrega
                    cur.execute("UPDATE sales SET ID_Sale = %s, Date = %s WHERE ID_Sale = %s", (idSale, date, id))
                    mysql.connection.commit()
                    cur.close()
                    if idSale != id:
                        id = idSale
                    flash(f"Venta número {idSale} actualizada correctamente.", "success")
                else:
                    flash("Ya existe una venta con esa clave o fecha.", "error")
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

    return redirect(url_for("updateSale", id=id))

# Close Sale Route
@app.route('/closeSale/<int:id>', methods=['GET'])
def closeSale(id):
    try:

        if 'ID_User' in session:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE sales SET Active = 'NO' WHERE ID_Sale = %s", (id,))
            mysql.connection.commit()
            flash("Venta cerrada correctamente.", "success")

        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
    return redirect(url_for("salesSection"))

# Detail Sales route
@app.route('/detailSaleSection/<int:id>', methods=['GET', 'POST'])
def detailSaleSection(id):
    try:
        if 'ID_User' in session:
            if request.method == 'GET':
                session.pop("SaleNumber", None)
                cur = mysql.connection.cursor()
                cur.execute("SELECT detail_sales.ID_DetailSale, detail_sales.ID_Sale, products.Name, detail_sales.Quantity, detail_sales.Price, detail_sales.Total FROM detail_sales JOIN products ON detail_sales.ID_Product = products.ID_Product WHERE ID_SALE = %s", (id,))
                sqlValue = cur.fetchall()
                total = []

                for register in sqlValue:
                    total.append(register[5])

                total = sum(total)
                cur.execute("SELECT * FROM products")
                sqlValue2 = cur.fetchall()
                cur.execute("SELECT Active FROM sales WHERE ID_Sale = %s", (id,))
                sqlValue3 = cur.fetchone()
                print(sqlValue3)
                cur.close()
                session["SaleNumber"] = id
                return render_template("detailSaleSection.html", allDeSales = sqlValue, allProducts=sqlValue2, totalSales = total, Activa = sqlValue3[0])

        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

# Add Sales Products route JSON
@app.route('/addSalesProducts', methods=['POST'])
def addSalesProducts():
    try:
        if 'ID_User' in session:
            if request.method == 'POST':
                jsonData = request.get_json()
                cur = mysql.connection.cursor()
                
                for index in jsonData.values():
                    for index2 in index:
                        productName = index2.get("name")
                        productQuantity = index2.get("quantity")
                        productPrice = index2.get("price").replace("$", "")
                        productTotal = index2.get("total").replace("$", "")
                        print(productName, productQuantity, productPrice, productTotal)
                        cur.execute("SELECT ID_Product FROM products WHERE Name = %s", (productName,))
                        indexProduct = cur.fetchone()

                        if indexProduct != None:
                            cur.execute("SELECT Quantity FROM products WHERE ID_Product = %s",(indexProduct,))
                            totalQuantity = cur.fetchone()[0]
                            newTotalQuantity = int(totalQuantity) - int(productQuantity)

                            cur.execute("INSERT INTO detail_sales (ID_Sale, ID_Product, Quantity, Price, Total) VALUES (1, %s, %s, %s, %s)", (indexProduct, productQuantity, productPrice, productTotal))
                            mysql.connection.commit()

                            cur.execute("UPDATE products SET Quantity = %s WHERE ID_Product = %s", (newTotalQuantity, indexProduct))
                            mysql.connection.commit()
                    cur.close()
                return jsonify(jsonData)

        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
    return redirect(url_for("detailSaleSection", id = session["SaleNumber"]))

# Detail Sales (ADD PRODUCTS) Route
@app.route('/addDetailSaleSection', methods=['POST'])
def addDetailSaleSection():
    try:
        if 'ID_User' in session:

            if request.method == "POST":
                idProduct = int(request.form["ID_Product"])
                quantity = int(request.form["Cantidad"])
                price = float(request.form["Precio"])
                totalPrice = float(request.form["Total"])

                cur = mysql.connection.cursor()
                cur.execute("SELECT Quantity FROM products WHERE ID_Product = %s", (idProduct,))
                sqlValue = cur.fetchone()
                saleQuantity = sqlValue[0]

                if sqlValue is not None:
                    if saleQuantity > 0 and quantity <= saleQuantity:
                        cur.execute("INSERT INTO detail_sales (Id_Sale, ID_Product, Quantity, Price, Total) VALUES (%s, %s, %s, %s, %s)", (session["SaleNumber"], idProduct, quantity, price, totalPrice))
                        mysql.connection.commit()
                        saleQuantity = saleQuantity - quantity
                        cur.execute("UPDATE products SET Quantity = %s WHERE ID_Product = %s ", (saleQuantity, idProduct))
                        mysql.connection.commit()
                        cur.close()
                    else:
                        flash("No se puede realizar la venta a falta de inventario.", "error")
                        cur.close()
                else:
                    cur.close()
                    flash("Error al obtener la información del producto.", "error")

        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

    return redirect(url_for("detailSaleSection", id = session["SaleNumber"]))

# Delete Product of Sale Route
@app.route('/deleteDetailSaleProduct/<int:id>', methods=['GET'])
def deleteDetailSaleProduct(id):
    try:

        if 'ID_User' in session:
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID_Product, Quantity FROM detail_sales WHERE ID_DetailSale = %s", (id,))
            sqlValue = cur.fetchone()
            cur.execute("DELETE FROM detail_sales WHERE ID_DetailSale = %s", (id,))
            mysql.connection.commit()
            cur.execute("UPDATE products SET Quantity = Quantity + %s WHERE ID_Product = %s", (sqlValue[1], sqlValue[0]))
            mysql.connection.commit()
            cur.close()
            flash("Venta eliminada correctamente.", "success")
        else:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

    return redirect(url_for("detailSaleSection", id = session["SaleNumber"]))

if __name__ == '__main__':
    app.run(debug=True, port=5000)