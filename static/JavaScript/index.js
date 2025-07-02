const confirmActions = (message) => confirm(message);

const dynamicNavBar = url => {
    const navBarImageLink = document.querySelector("#navigationBarContainer").children[0];
    navBarImageLink.setAttribute("href", url);
    // console.log(navBarImageLink.getAttribute("href"))
}

const openUpdateProductWindow = (button) => {
    const url = button.getAttribute("data-url");

    if (navigator.userAgent.match(/Android/i) || navigator.userAgent.match(/webOS/i) || navigator.userAgent.match(/iPhone/i) || navigator.userAgent.match(/iPad/i) || navigator.userAgent.match(/iPod/i) || navigator.userAgent.match(/BlackBerry/i) || navigator.userAgent.match(/Windows Phone/i)) {
        window.open(url, '_self', ',menubar=0, location=yes, resizable=0, scrollbars=1, status=1, titlebar=1')
    } else {
        window.open(url, '_blank', ',menubar=0, location=yes, resizable=0, scrollbars=1, status=1, titlebar=1, width=640,height=600');
    }
}

const searchTableValue = (inputName, cellNumber) => {
    const input = document.querySelector('#' + inputName).value.toLowerCase();
    const tBody = document.querySelector("#tBody");
    const rows = tBody.getElementsByTagName("tr");

    for (let i = 0; i < rows.length; i++) {
        const productNameCell = rows[i].getElementsByTagName("td")[cellNumber];
        console.log(productNameCell);

        if (productNameCell) {
            const productName = productNameCell.innerText.toLowerCase();

            if (productName.includes(input)) {
                rows[i].style.display = "";
            } else {
                rows[i].style.display = "none";
            }
        }
    }
}

const getPriceProduct = () => {
    const productSelect = document.querySelector("#ID_Product");
    const selectedOption = productSelect.selectedOptions[0];

    if (!selectedOption || selectedOption.disabled) {
        return false;
    }

    let productPrice = selectedOption.getAttribute("data-price");
    let productPiece = selectedOption.getAttribute("data-piece");

    if (productPrice && productPiece) {
        let productQuantity = document.querySelector("#Cantidad");

        productQuantity.value = 1;
        document.querySelector("#Total").value = productPrice;
        document.querySelector("#Precio").value = productPrice;

        productQuantity.removeAttribute("readonly");
        document.querySelector("#quantityAvailable").innerText = "Cantidad disponible: " + productPiece;
        productQuantity.setAttribute("max", productPiece);
    }
}

const calculateTotalPrice = () => {
    let productQuantity = document.querySelector("#Cantidad").value;
    let productID = document.querySelector("#ID_Product").value;

    if (productQuantity > 0 && productID) {
        let productPrice = document.querySelector("#Precio").value;
        productPrice = parseFloat(productPrice);
        let totalPrice = productPrice * productQuantity;
        document.querySelector("#Total").value = totalPrice.toFixed(2);
    }
}

const calculateTotalCost = () => {
    let productQuantity = document.querySelector("#Cantidad").value;
    let productCost = document.querySelector("#CostoUnidad").value;

    if (productQuantity > 0 && productCost > 0) {
        productCost = parseFloat(productCost);
        let totalCost = productCost * productQuantity;
        document.querySelector("#CostoTotal").value = totalCost.toFixed(2);
    } else {
        document.querySelector("#CostoTotal").value = 0;
    }
}

const deleteProductSale = (Id) => {
    let row = Id.parentNode.parentNode;
    let tableProductSales = document.querySelector("#salesProductsTable");
    let productSelect = document.querySelector("#ID_Product");
    let selectedProductOption = productSelect.selectedOptions[0]; //el option seleccionado de select
    let allSelectOptions = productSelect.children; //todos los option del select
    let TotalSale = document.querySelector("#totalProductSales").innerText.replace("$", "");
    let productName = row.children[1].innerText;
    let productQuantitySale = row.children[2].innerText;
    let totalProductSale = row.children[4].innerText.replace("$", "");
    let newTotalSale = 0;
    let productQuantity = selectedProductOption.getAttribute("data-piece");
    let newTotalQuantity = 0;
    let inputQuantity = document.querySelector("#Cantidad");
    let price = 0;
    const allProductNames = [];
    let productIndexOption = 0;
    let productUpdate = "";
    let noSelectedProductQuantity = undefined;
    let totalInput = document.querySelector("#Total");
    let precioInput = document.querySelector("#Precio");

    newTotalSale = parseFloat(TotalSale) - parseFloat(totalProductSale); // Restar del total general el total del producto a eliminar
    tableProductSales.deleteRow(row.rowIndex); //Elimina la fila 
    document.querySelector("#totalProductSales").innerText = "$" + newTotalSale; //asigna el nuevo total al elemento
    newTotalQuantity = parseInt(productQuantity) + parseInt(productQuantitySale); //Suma a la cantidad total del producto la cantidad vendida eliminada

    for (let index = 0; index < allSelectOptions.length; index++) {
        allProductNames.push(allSelectOptions[index].innerText);
    }

    if (selectedProductOption.innerText == productName) { // Si el usuario va a eliminar el producto vendido MIENTRAS TIENE SELECCIONADO EL MISMO PRODUCTO
        selectedProductOption.setAttribute("data-piece", newTotalQuantity);
        price = selectedProductOption.getAttribute("data-price");
        inputQuantity.setAttribute("max", newTotalQuantity);
        document.querySelector("#quantityAvailable").innerText = "Cantidad disponible: " + newTotalQuantity;

    } else if (selectedProductOption.innerText == productName + " (No disponible)") { // Si el producto a eliminar ESTA SELECIONADO POR EL USUARIO Y ADEMAS SE QUEDO SIN EXISTENCIAS
        price = selectedProductOption.getAttribute("data-price");
        inputQuantity.value = 1;
        inputQuantity.setAttribute("max", newTotalQuantity);
        totalInput.value = price;
        precioInput.value = price;
        inputQuantity.removeAttribute("readonly");
        selectedProductOption.innerText = productName;
        selectedProductOption.setAttribute("data-piece", newTotalQuantity);
        selectedProductOption.removeAttribute("disabled");
        document.querySelector("#quantityAvailable").innerText = "Cantidad disponible: " + newTotalQuantity;
    } else {
        // EL USUARIO NO TIENE SELECIONADO EL PRODUCTO , PERO EL PRODUCTO SE QUEDO CON EXISTENCIAS.
        if (allProductNames.indexOf(productName) !== -1) {
            productIndexOption = allProductNames.indexOf(productName);
            productUpdate = allSelectOptions[productIndexOption];
            noSelectedProductQuantity = productUpdate.getAttribute("data-piece");
            newTotalQuantity = parseInt(noSelectedProductQuantity) + parseInt(productQuantitySale);
            productUpdate.setAttribute("data-piece", newTotalQuantity);
        // EL USUARIO NO TIENE SELECIONADO EL PRODUCTO , PERO EL PRODUCTO SE QUEDO SIN EXISTENCIAS.
        } else {
            productIndexOption = allProductNames.indexOf(productName + " (No disponible)");
            productUpdate = allSelectOptions[productIndexOption];
            noSelectedProductQuantity = productUpdate.getAttribute("data-piece");
            newTotalQuantity = parseInt(noSelectedProductQuantity) + parseInt(productQuantitySale);
            productUpdate.innerText = productName;
            productUpdate.setAttribute("data-piece", newTotalQuantity);
            productUpdate.removeAttribute("disabled");
        }
    }
}

const saleAllProducts = () => {
    const table = document.querySelector('#tableBody');
    let productsToSale = undefined;
    const allproductsToSaleValue = [];

    if (table.children.length > 0) {
        let action = confirmActions("¿Realizar venta de los productos?");
        if (action) {
            console.log(table.children)
        productsToSale = table.children;

        for (let index = 0; index < productsToSale.length; index++) {
            const product = { name: productsToSale[index].children[1].innerHTML, quantity: productsToSale[index].children[2].innerHTML, price: productsToSale[index].children[3].innerHTML, total: productsToSale[index].children[4].innerHTML };
            allproductsToSaleValue.push(product)
        }

        fetch('/addSalesProducts', {
            headers: { 'Content-Type': 'application/json' }, method: 'POST',
            body: JSON.stringify({
                'Lista': allproductsToSaleValue
            })
        })
            .then(function (response) {

                if (response.ok) {
                    response.json();
                    table.innerHTML = "";
                    document.querySelector("#totalProductSales").innerText = "$0";
                    alert("Venta realizada con éxito.");
                        // .then(function (response) {
                        //     console.log(response);
                        // });
                }
                else {
                    throw Error('Algo salío mal.');
                }
            })
            .catch(function (error) {
                console.log(error);
            });
        console.log(allproductsToSaleValue);
        }

    } else {
        alert("No ha agregado productos para vender.");
    }
}