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

        if not sqlValue:
            flash("No existe este usuario.", "error")
            return redirect(url_for("index"))

        # Si sqlValue no es nulo, comprueba si la contraseña es la misma.
        isChecked = bcrypt.checkpw(Password.encode('utf-8'), sqlValue[1].encode('utf-8'))

        if not isChecked:
            flash("El usuario y/o la contraseña son incorrectos.", "error")
            return redirect(url_for("index"))

        # Si es la misma contraseña (true) asigna cookies.
        session["ID_User"] = sqlValue[0]
        session["User_Name"] = sqlValue[2]
        return redirect(url_for("productsSection"))

    return render_template("index.html")

# Logout Route
@app.route('/logout')
def logout():
    session.pop("ID_User", None)
    session.pop("ResUser", None)
    session.pop("CodeForPw", None)
    session.pop("User_Name", None)
    session.pop("SaleNumber", None)
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("index"))

# Password Recovery Route
@app.route('/passwordRecovery', methods = ['GET', 'POST'])
def passwordRecovery():
    session.pop("ResUser", None)
    session.pop("CodeForPw", None)

    if request.method == "POST":
        emailUser = request.form["Email"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT NameUser FROM users WHERE Email = %s", (emailUser,))
        sqlValue = cur.fetchone()
        cur.close()

        if not sqlValue:
            flash("No existe un usuario con este correo en el sistema.", "error")
            return redirect(url_for("passwordRecovery"))

        # Si sqlValue no es nulo, manda un correo al usuario.
        codeSixDigits = codeGenerate()
        message = "Abarrotes Patch \nHola, tu código de recuperación para restablecer su contraseña es: " + codeSixDigits
        sendEmail = sendSimpleEmail(os.getenv("MY_EMAIL"), emailUser, message, "Código para restablecer su Contraseña")

        if sendEmail == False:
            flash("No se pudo enviar el correo electrónico.", "error")
            return redirect(url_for("passwordRecovery"))

        # Si no hay error al enviar el email.
        session["CodeForPw"] = codeSixDigits
        print(codeSixDigits)
        session['ResUser'] = sqlValue[0]
        return redirect(url_for("passwordUpdate"))

    return render_template("passwordRecovery.html")

# Password Update Route
@app.route('/passwordUpdate', methods = ['GET', 'POST'])
def passwordUpdate():
    try:
        if 'ResUser' not in session:
            return redirect(url_for("index"))

        if request.method == "POST":
            Code = request.form["Code"].upper()
            newPassword = request.form["Pass"]

            # Si el codigo es diferente del codigo de la cookie volver a intentar.
            if Code != session["CodeForPw"]:
                flash("El código ingresado es incorrecto.", "error")
                return redirect(url_for("passwordUpdate"))

            #Si el codigo es el mismo al de la cookie, permitir actualizar password.
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

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")

    return render_template("updatePassword.html")

# Products Route
@app.route('/productsSection', methods = ['GET'])
def productsSection():
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        #Si el usuario inicio sesión permitir mostrar los productos
        if request.method == "GET":
            cur = mysql.connection.cursor()
            cur.execute("SELECT P.ID_Product, V.Name, P.Name, P.Cost, P.Price, P.Quantity, P.Expiration_Date, P.Description FROM products AS P INNER JOIN vendors AS V ON P.ID_Vendor = V.ID_Vendor")
            sqlValue = cur.fetchall()
            # print(sqlValue)
            cur.close()
            return render_template("productsSection.html", allProducts = sqlValue)

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("productsSection"))


# Add Product Route
@app.route('/addProduct', methods = ['GET', 'POST'])
def addProduct():
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "GET":
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM products")
            sqlValue = cur.fetchall()
            cur.execute("SELECT ID_Vendor, Name FROM vendors")
            sqlValue2 = cur.fetchall()
            cur.close()
            return render_template("newProductSection.html", allProducts = sqlValue, allVendors = sqlValue2)

        if request.method == 'POST':
            # idProduct = int (request.form["ID"])
            name = request.form["Nombre"]
            cost = float(request.form["Costo"])
            price = float(request.form["Precio"])
            date = request.form["Fecha"]
            description = request.form["Descripcion"]
            vendor = request.form["IDVendor"]
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID_Product FROM products WHERE Name = %s", (name,))
            sqlValue = cur.fetchone()

            if sqlValue: # Si es "true" existe un producto con ese nombre. NO lo agrega.
                flash("Ya existe un producto con este nombre.", "error")
                return redirect(url_for("addProduct"))

            if not date:
                cur.execute("INSERT INTO products (Name, Cost, Price, Quantity, Description, ID_Vendor) VALUES (%s, %s, %s, 0, %s, %s)", (name, cost, price, description, vendor))
            else:
                cur.execute("INSERT INTO products (Name, Cost, Price, Quantity, Expiration_Date, Description, ID_Vendor) VALUES (%s, %s, %s, 0, %s, %s, %s)", (name, cost, price, date, description, vendor))

            mysql.connection.commit()
            cur.close()
            flash(f"Producto \"{name}\" agregado correctamente.", "success")
            return redirect(url_for("addProduct"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("addProduct"))

# Delete Product Route
@app.route('/deleteProduct/<int:idProduct>', methods = ['GET'])
def deleteProduct(idProduct):
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        cur = mysql.connection.cursor()
        cur.execute("SELECT ID FROM orders WHERE ID_Product = %s", (idProduct,))
        sqlValue = cur.fetchall()

        if sqlValue: # Si existen ordenes asociadas con ese ID (producto) no lo elimina.
            cur.close()
            sqlValue = [str(i[0]) for i in sqlValue]
            sqlValue = ', '.join(sqlValue)
            flash(f"No se puede eliminar el producto ya que tiene compras asociadas. Compra(s) número: {sqlValue}", "error")
            return redirect(url_for("productsSection"))

        # Si no existen ordenes asociadas, elimina el producto.
        cur.execute("DELETE FROM products WHERE ID_Product = %s", (idProduct,))
        mysql.connection.commit()
        cur.close()
        flash("Producto eliminado correctamente.", "success")
        return redirect(url_for("productsSection"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("productsSection"))

# Update Product Route
@app.route(('/updateProduct/<int:idProduct>'), methods = ['GET', 'POST'])
def updateProduct(idProduct):

    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "GET":
            cur = mysql.connection.cursor()
            cur.execute("SELECT P.ID_product, V.Name, P.Name, P.Cost, P.Price, P.Quantity, P.Expiration_Date, P.Description FROM products AS P INNER JOIN vendors AS V ON P.ID_Vendor = V.ID_Vendor WHERE ID_Product = %s", (idProduct,))
            sqlValue = cur.fetchone()
            cur.execute("SELECT ID_Vendor, Name FROM vendors")
            sqlValue2 = cur.fetchall()
            cur.close()
            return render_template("updateProductSection.html", producto = sqlValue, allVendors = sqlValue2)

        if request.method == "POST":
            # idProduct = int (request.form["IDProducto"])
            name = request.form["Nombre"]
            cost = float(request.form["Costo"])
            price = float(request.form["Precio"])
            date = request.form["Fecha"]
            description = request.form["Descripcion"]
            vendor = request.form["IDVendor"]
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID_Product FROM products WHERE Name = %s AND ID_product != %s", (name, idProduct))
            sqlValue3 = cur.fetchone()

            if sqlValue3: # Si existe un producto con ese nombre (sin incluir este), actualiza todo menos Nombre.
                if not date:
                    cur.execute("UPDATE products SET Cost = %s, Price = %s, Expiration_Date = NULL, Description = %s, ID_Vendor = %s WHERE ID_Product = %s", (cost, price, description, vendor, idProduct))
                else:
                    cur.execute("UPDATE products SET Cost = %s, Price = %s, Expiration_Date = %s, Description = %s, ID_Vendor = %s WHERE ID_Product = %s", (cost, price, date, description, vendor, idProduct))

                mysql.connection.commit()
                cur.close()
                flash("No se actualizo el nombre por que ya existe un producto con ese mismo.", "success")
                return redirect(url_for("updateProduct", idProduct = idProduct))

            if not date: #Si es "false" sqlValue3, no existe un producto llamado asi y actualiza todos los datos.
                cur.execute("UPDATE products SET Name = %s, Cost = %s, Price = %s, Expiration_Date = NULL, Description = %s, ID_Vendor = %s WHERE ID_Product = %s", (name, cost, price, description, vendor, idProduct))
            else:
                cur.execute("UPDATE products SET Name = %s, Cost = %s, Price = %s, Expiration_Date = %s, Description = %s, ID_Vendor = %s WHERE ID_Product = %s", (name, cost, price, date, description, vendor, idProduct))

            mysql.connection.commit()
            cur.close()
            flash("Todos los campos del producto se actualizaron correctamente.", "success")
            return redirect(url_for("updateProduct", idProduct = idProduct))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("updateProduct", idProduct = idProduct))

# User Profile Route
@app.route('/userProfile', methods=['GET', 'POST'])
def userProfile():
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "GET":
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID_User, NameUser, Email FROM users WHERE ID_User = %s", (session["ID_User"],))
            sqlValue = cur.fetchone()
            cur.close()
            return render_template("userProfileSection.html", dataUser = sqlValue)

        if request.method == 'POST':
            name = request.form["Nombre"]
            email = request.form["Correo"]
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID_User FROM users WHERE (NameUser = %s OR Email = %s) AND NameUser!=%s", (name, email, session["User_Name"]))
            sqlValue = cur.fetchone()

            if sqlValue: # Si es "true" existe un usuario con ese correo o nombre lo actualiza
                flash("El usuario o correo ya existen.", "success")
                return redirect(url_for("userProfile"))

            # Si no existe un usuario con ese correo o Nombre, actualiza los datos.
            cur.execute("UPDATE users SET NameUser = %s, Email = %s WHERE ID_User = %s", (name, email, session["ID_User"]))
            mysql.connection.commit()
            cur.close()
            session["User_Name"] = name
            flash("Usuario actualizado correctamente.", "success")
            return redirect(url_for("userProfile"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("userProfile"))

# Vendors Route
@app.route('/vendorsSection', methods=['GET'])
def vendorsSection():
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM vendors")
        sqlValue = cur.fetchall()
        cur.close()
        return render_template("vendorsSection.html", allVendors = sqlValue)

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("vendorsSection"))

# Ruta para añadir un nuevo vendedor 
@app.route('/addNewVendor', methods = ['GET','POST'])
def addNewVendor():
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "POST":
            # idVendor = int(request.form["IDVendor"])
            name = request.form["Nombre"]
            number = request.form["Numero"]
            date = request.form["Dia"]
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID_Vendor FROM vendors WHERE Name = %s OR Number = %s", (name, number))
            sqlValue = cur.fetchone()

            if sqlValue: #Si es "true" existe un producto con ese nombre o ID.
                flash("El nombre y/o teléfono del proveedor ya existe.", "error")
                return redirect(url_for("addNewVendor"))

            cur.execute("INSERT INTO vendors (Name, Number, Visit_Day) VALUES (%s, %s, %s)", (name, number, date))
            mysql.connection.commit()
            cur.close()
            flash(f"Proveedor \"{name}\" agregado correctamente.", "success")
            return redirect(url_for("addNewVendor"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("addNewVendor"))

    return render_template("newVendorSection.html")

# Delete Vendor Route
@app.route('/deleteVendor/<int:idVendor>', methods = ['GET'])
def deleteVendor(idVendor):
    try:

        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        cur = mysql.connection.cursor()
        cur.execute("SELECT ID FROM orders WHERE ID_Vendor = %s;", (idVendor,))
        associatedOrders = cur.fetchall()
        cur.execute("SELECT Name FROM products WHERE ID_Vendor = %s;", (idVendor,))
        associatedVendors = cur.fetchone()

        if associatedOrders or associatedVendors: # Si es "true" no lo elimina por que tiene compras y/o productos asignadas 
            cur.close()
            flash("No se puede eliminar el proveedor ya que tiene compras y/o productos asociados.", "error")
            return redirect(url_for("vendorsSection"))

        cur.execute("DELETE FROM vendors WHERE ID_Vendor = %s;", (idVendor,))
        mysql.connection.commit()
        cur.close()
        flash("Proveedor eliminado correctamente.", "success")
        return redirect(url_for("vendorsSection"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("vendorsSection"))

# Update Vendor Route
@app.route(('/updateVendor/<int:idVendor>'), methods = ['GET', 'POST'])
def updateVendor(idVendor):
    try:

        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "GET":
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM vendors WHERE ID_Vendor = %s", (idVendor,))
            sqlValue = cur.fetchone()
            cur.close()
            return render_template("updateVendorSection.html", proveedor = sqlValue)

        if request.method == "POST":
            # idVendor = int(request.form["IDVendor"])
            name = request.form["Nombre"]
            number = request.form["Numero"]
            date = request.form["Dia"]
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID_Vendor FROM vendors WHERE (Name = %s OR Number = %s) AND ID_Vendor != %s", (name, number, idVendor))
            sqlValue = cur.fetchall()

            if sqlValue: #Si es "true"  existen otros proveedores con los mismos datos.
                cur.close()
                flash("No se actualizaron los datos ya que el nombre y/o teléfono ya existen.", "error")
                return redirect(url_for("updateVendor", idVendor = idVendor))

            cur.execute("SELECT ID FROM orders WHERE ID_Vendor = %s",(idVendor,))
            vendorOrdesExist = cur.fetchall()

            if vendorOrdesExist:
                flash("No se puede actualizar el ID por que tiene compras asociadas.", "error")
                return redirect(url_for("updateVendor", idVendor = idVendor))

            # Si no hay asociados, actualiza los datos del proveedor
            cur.execute("UPDATE vendors SET Name = %s, Number = %s, Visit_Day = %s WHERE ID_Vendor = %s", (name, number, date, idVendor))
            mysql.connection.commit()
            cur.close()
            flash(f"Los campos del proveedor \"{name}\" fueron actualizados.", "success")
            return redirect(url_for("updateVendor", idVendor = idVendor))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("updateVendor", idVendor = idVendor))

# Orders Route
@app.route('/ordersSection', methods = ['GET'])
def ordersSection():
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "GET":
            cur = mysql.connection.cursor()
            cur.execute("SELECT orders.ID, products.Name, vendors.Name, orders.Quantity, orders.Unit_Cost, orders.Cost, orders.Date FROM orders JOIN vendors ON orders.ID_Vendor = vendors.ID_Vendor JOIN products ON orders.ID_Product = products.ID_Product ORDER BY orders.ID")
            sqlValue = cur.fetchall()
            cur.close()
            return render_template("ordersSection.html", allOrders = sqlValue)

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("ordersSection"))

# Add Order Route
@app.route('/addOrder', methods = ['GET', 'POST'])
def addOrder():
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "GET":
            cur = mysql.connection.cursor()
            cur.execute("SELECT ID_Vendor, Name FROM vendors")
            sqlValue = cur.fetchall()
            cur.execute("SELECT ID_Product, Name FROM products")
            sqlValue2 = cur.fetchall()
            cur.close()
            return render_template("newOrderSection.html", allIDVendors = sqlValue, allIDProducts = sqlValue2)

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

            if sqlValue: # Si existe una orden con ese ID NO lo agrega.
                cur.close()
                flash(f"Ya existe una compra con la clave \"{idOrder}\" clave.", "error")
                return redirect(url_for("addOrder"))

            cur.execute("SELECT P.Name, V.Name FROM products AS P INNER join vendors AS V ON P.ID_Vendor = V.ID_Vendor WHERE P.ID_Product = %s AND V.ID_Vendor = %s;", (idProduct, idVendor))
            vendorProducts = cur.fetchone()
            print(idVendor, idProduct)

            if not vendorProducts: #Si es "false" el producto a comprar NO LO VENDE el vendedor.
                cur.close()
                flash("El producto a comprar no lo distribuye el proveedor seleccionado.", "error")
                return redirect(url_for("addOrder"))

            cur.execute("INSERT INTO orders (ID, ID_Vendor, ID_Product, Quantity, Unit_Cost, Cost, Date) VALUES (%s, %s, %s, %s, %s, %s, %s)", (idOrder, idVendor, idProduct, quantity, unitCost ,Totalcost, date))
            cur.execute("UPDATE products SET Quantity = Quantity + %s WHERE ID_Product = %s", (quantity, idProduct))
            mysql.connection.commit()
            cur.close()
            flash(f"Compra número \"{idOrder}\" agregada correctamente.", "success")
            return redirect(url_for("addOrder"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("addOrder"))

# Delete Order Route
@app.route('/deleteOrder/<int:idOrder>', methods = ['GET'])
def deleteOrder(idOrder):
    try:

        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        cur = mysql.connection.cursor()
        cur.execute("SELECT ID_Product, Quantity FROM orders WHERE ID = %s", (idOrder,))
        sqlValue = cur.fetchone()
        cur.execute("DELETE FROM orders WHERE ID = %s", (idOrder,))
        cur.execute("UPDATE products SET Quantity = Quantity - %s WHERE ID_Product = %s", (sqlValue[1], sqlValue[0]))
        mysql.connection.commit()
        cur.close()
        flash("Compra eliminada correctamente.", "success")
        return redirect(url_for("ordersSection"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("ordersSection"))

# Actualizar Compra
@app.route(('/updateOrder/<int:oldIdOrder>'), methods = ['GET', 'POST'])
def updateOrder(oldIdOrder):
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "GET":
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM orders WHERE ID = %s;", (oldIdOrder,))
            sqlValue = cur.fetchone()
            cur.execute("SELECT ID_Vendor, Name FROM vendors;")
            sqlValue2 = cur.fetchall()
            cur.execute("SELECT ID_Product, Name FROM products;")
            sqlValue3 = cur.fetchall()
            cur.close()
            return render_template("updateOrderSection.html", compra = sqlValue, allIDVendors = sqlValue2, allIDProducts = sqlValue3)

        if request.method == "POST":
            newIdOrder = int(request.form["ID"])
            idVendor = int(request.form["IDVendor"])
            idProduct = int(request.form["ID_Product"])
            unitCost = float(request.form["CostoUnidad"])
            Totalcost = float(request.form["CostoTotal"])
            quantity = int(request.form["Cantidad"])
            date = request.form["Fecha"]

            cur = mysql.connection.cursor()
            cur.execute("SELECT ID_Product, Quantity FROM orders WHERE ID = %s;", (oldIdOrder,))
            idProductDB, quantityDB = cur.fetchone()
            cur.execute("SELECT * FROM orders WHERE ID = %s AND ID != %s;", (newIdOrder, oldIdOrder))
            sqlValue = cur.fetchone()

            # Comprueba si el proveedor vende el producto de la orden a actualizar.
            cur.execute("SELECT P.Name, V.Name FROM products AS P INNER join vendors AS V ON P.ID_Vendor = V.ID_Vendor WHERE P.ID_Product = %s AND V.ID_Vendor = %s;", (idProduct, idVendor))
            vendorProducts = cur.fetchone()

            if not vendorProducts: #Si es "false" el producto a comprar NO LO VENDE el vendedor.
                cur.close()
                flash("El producto a comprar no lo distribuye el proveedor seleccionado.", "error")
                return redirect(url_for("updateOrder", oldIdOrder = oldIdOrder))

            if sqlValue: # Si es "true" ya existe una compra con esa clave que no sea esta misma, NO se actualiza el ID solo el resto
                cur.execute("UPDATE orders SET ID_Vendor = %s, ID_Product = %s, Quantity = %s, Unit_Cost = %s, Cost = %s, Date = %s WHERE ID = %s;", (idVendor, idProduct, quantity, unitCost, Totalcost, date, oldIdOrder))
                message = f"No se actualizo el ID por que ya existe una compra con este mismo ({newIdOrder})."
            else:
                cur.execute("UPDATE orders SET ID = %s, ID_Vendor = %s, ID_Product = %s, Quantity = %s, Unit_Cost = %s, Cost = %s, Date = %s WHERE ID = %s;", (newIdOrder, idVendor, idProduct, quantity, unitCost, Totalcost, date, oldIdOrder))
                message = f"Todos los datos de la compra número {oldIdOrder} fueron actualizados correctamente."

            cur.execute("UPDATE products SET Quantity = Quantity - %s WHERE ID_Product = %s;", (quantityDB, idProductDB))
            cur.execute("UPDATE products SET Quantity = Quantity + %s WHERE ID_Product = %s;", (quantity, idProduct))
            mysql.connection.commit()
            cur.close()
            flash(message, "success")

            if not sqlValue:
                return redirect(url_for("updateOrder", oldIdOrder = newIdOrder))
            else:
                return redirect(url_for("updateOrder", oldIdOrder = oldIdOrder))

    except Exception as error:
        print(error)
        flash(f"Ocurrió un error: {error}.", "error")
        return redirect(url_for("updateOrder", oldIdOrder = oldIdOrder))

# Sales Route
@app.route('/salesSection', methods = ['GET'])
def salesSection():
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "GET":
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM sales;")
            sqlValue = cur.fetchall()
            cur.close()
            return render_template("salesSection.html", allSales = sqlValue)

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("salesSection"))

# Add Sale Route
@app.route('/addSale', methods = ['GET', 'POST'])
def addSale():
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "GET":
            return render_template("newSaleSection.html")

        if request.method == "POST":
            idSale = request.form["ID"]
            date = request.form["Fecha"]
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM sales WHERE ID_Sale = %s OR Date = %s;", (idSale, date))
            sqlValue = cur.fetchone()

            if sqlValue: # Si es "true" ya existe una venta con ese ID y fecha. NO lo agrega.
                flash("Ya existe una venta con esa clave o fecha.", "error")
                return render_template("newSaleSection.html")

            cur.execute("INSERT INTO sales (ID_Sale, Date, Active) VALUES (%s, %s,'SI')", (idSale, date))
            mysql.connection.commit()
            cur.close()
            flash(f"Venta número \"{idSale}\" agregada correctamente.", "success")
            return redirect(url_for("addSale"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return render_template("newSaleSection.html")

# Update Sale Route
@app.route('/updateSale/<int:oldIdSale>', methods = ['GET', 'POST'])
def updateSale(oldIdSale):
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == "GET":
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM sales WHERE ID_Sale = %s", (oldIdSale,))
            sqlValue = cur.fetchone()
            cur.close()
            return render_template("updateSaleSection.html", venta = sqlValue)

        if request.method == "POST":
            newIdSale = request.form["ID"]
            date = request.form["Fecha"]
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM sales WHERE (ID_Sale = %s OR Date = %s) AND ID_Sale != %s", (newIdSale, date, oldIdSale))
            sqlValue = cur.fetchone()

            if sqlValue: # Si es "true" ya hay una venta con esa clave o fecha.
                cur.close()
                flash("Ya existe una venta con esa clave o fecha.", "error")
                return redirect(url_for("updateSale", oldIdSale = oldIdSale))

            cur.execute("UPDATE sales SET ID_Sale = %s, Date = %s WHERE ID_Sale = %s", (newIdSale, date, oldIdSale))
            cur.execute("UPDATE detail_sales SET ID_Sale = %s WHERE ID_Sale = %s",(newIdSale, oldIdSale))
            mysql.connection.commit()
            cur.close()
            flash(f"Venta número \"{oldIdSale}\" actualizada correctamente.", "success")
            
            if not sqlValue:
                return redirect(url_for("updateSale", oldIdSale = newIdSale ))
            else:
                return redirect(url_for("updateSale", oldIdSale = oldIdSale))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("updateSale", oldIdSale = oldIdSale))

# Close Sale Route
@app.route('/closeSale/<int:idSale>', methods = ['GET'])
def closeSale(idSale):
    try:

        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        cur = mysql.connection.cursor()
        cur.execute("UPDATE sales SET Active = 'NO' WHERE ID_Sale = %s", (idSale,))
        mysql.connection.commit()
        flash("Venta cerrada correctamente.", "success")
        return redirect(url_for("salesSection"))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("salesSection"))

# Detail Sales route
@app.route('/detailSaleSection/<int:idSale>', methods = ['GET'])
def detailSaleSection(idSale):
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == 'GET':
            session.pop("SaleNumber", None)
            cur = mysql.connection.cursor()
            cur.execute("SELECT DS.ID_DetailSale, DS.ID_Sale, products.Name, DS.Quantity, DS.Price, DS.Total FROM detail_sales AS DS JOIN products ON DS.ID_Product = products.ID_Product WHERE ID_SALE = %s", (idSale,))
            sqlValue = cur.fetchall()
            cur.execute("SELECT * FROM products")
            sqlValue2 = cur.fetchall()
            cur.execute("SELECT Active FROM sales WHERE ID_Sale = %s", (idSale,))
            sqlValue3 = cur.fetchone()
            cur.close()
            session["SaleNumber"] = idSale
            return render_template("detailSaleSection.html", allDeSales = sqlValue, allProducts = sqlValue2, Activa = sqlValue3[0])

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("detailSaleSection", idSale = idSale))

# Add Sales Products route JSON
@app.route('/addSalesProducts', methods = ['POST'])
def addSalesProducts():
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == 'POST':
            jsonData = request.get_json()
            cur = mysql.connection.cursor()

            for JSlist in jsonData.values():
                for product in JSlist:
                    productName = product.get("name")
                    productQuantity = product.get("quantity")
                    productPrice = product.get("price").replace("$", "")
                    productTotal = product.get("total").replace("$", "")
                    print(productName, productQuantity, productPrice, productTotal)
                    cur.execute("SELECT ID_Product FROM products WHERE Name = %s", (productName,))
                    indexProduct = cur.fetchone()

                    if indexProduct:
                        cur.execute("SELECT Quantity FROM products WHERE ID_Product = %s",(indexProduct,))
                        totalQuantity = cur.fetchone()[0]
                        newTotalQuantity = int(totalQuantity) - int(productQuantity)
                        cur.execute("INSERT INTO detail_sales (ID_Sale, ID_Product, Quantity, Price, Total) VALUES (%s, %s, %s, %s, %s)", (session["SaleNumber"], indexProduct, productQuantity, productPrice, productTotal))
                        cur.execute("UPDATE products SET Quantity = %s WHERE ID_Product = %s", (newTotalQuantity, indexProduct))
                        mysql.connection.commit()
            cur.close()
            return jsonify(jsonData)

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("detailSaleSection", idSale = session["SaleNumber"]))

# All products sale Route
@app.route("/allProductsSaleSection/<int:idSale>", methods = ['GET'])
def allProductsSaleSection(idSale):
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        if request.method == 'GET':
            session.pop("SaleNumber", None)
            cur = mysql.connection.cursor()
            cur.execute("SELECT detail_sales.ID_DetailSale, detail_sales.ID_Sale, products.Name, detail_sales.Quantity, detail_sales.Price, detail_sales.Total FROM detail_sales JOIN products ON detail_sales.ID_Product = products.ID_Product WHERE ID_SALE = %s", (idSale,))
            sqlValue = cur.fetchall()
            cur.execute("SELECT Active FROM sales WHERE ID_Sale = %s", (idSale,))
            sqlValue2 = cur.fetchone()[0]
            cur.close()
            session["SaleNumber"] = idSale
            return render_template("allProductsSaleSection.html", allProductsSale = sqlValue, Active = sqlValue2)

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("allProductsSaleSection", idSale = idSale))

# Delete Product of Sale Route
@app.route('/deleteDetailSaleProduct/<int:idProduct>', methods = ['GET'])
def deleteDetailSaleProduct(idProduct):
    try:
        if 'ID_User' not in session:
            flash("No has iniciado sesión.", "error")
            return redirect(url_for("index"))

        cur = mysql.connection.cursor()
        cur.execute("SELECT ID_Product, Quantity FROM detail_sales WHERE ID_DetailSale = %s", (idProduct,))
        IDProductDB, quantityDB = cur.fetchone()
        cur.execute("DELETE FROM detail_sales WHERE ID_DetailSale = %s", (idProduct,))
        cur.execute("UPDATE products SET Quantity = Quantity + %s WHERE ID_Product = %s", (quantityDB, IDProductDB))
        mysql.connection.commit()
        cur.close()
        flash("Producto eliminado de la venta correctamente.", "success")
        return redirect(url_for("allProductsSaleSection", idSale = session["SaleNumber"]))

    except Exception as error:
        print(error)
        flash(f"Ocurrio un error: {error}.", "error")
        return redirect(url_for("allProductsSaleSection", idSale = session["SaleNumber"]))

if __name__ == '__main__':
    app.run(debug = True, port = 5000)