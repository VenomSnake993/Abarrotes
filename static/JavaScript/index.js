confirmActions = function (message) {
    return confirm(message);
}

dynamicNavBar = function (url) {
    let navBarImageLink = document.getElementById("navigationBarContainer").children[0];
    navBarImageLink.setAttribute("href", url)
    console.log(navBarImageLink.getAttribute("href"))
}

openUpdateProductWindow = function (button) {
    let url = button.getAttribute("data-url");

    if (navigator.userAgent.match(/Android/i) || navigator.userAgent.match(/webOS/i) || navigator.userAgent.match(/iPhone/i) || navigator.userAgent.match(/iPad/i) || navigator.userAgent.match(/iPod/i) || navigator.userAgent.match(/BlackBerry/i) || navigator.userAgent.match(/Windows Phone/i)) {
        console.log("Estás usando un dispositivo móvil!!");
        window.open(url, '_self', ',menubar=0, location=yes, resizable=0, scrollbars=1, status=1, titlebar=1')
    } else {
        console.log("No estás usando un móvil");
        window.open(url, '_blank', ',menubar=0, location=yes, resizable=0, scrollbars=1, status=1, titlebar=1, width=640,height=600');
    }

}

getPriceProduct = function () {
    let productSelect = document.querySelector("#ID_Product");
    let selectedOption = productSelect.selectedOptions[0];
    // console.log(productSelect)
    // console.log(selectedOption)
    if (!selectedOption || selectedOption.disabled) {
        return;
    }

    let productPrice = selectedOption.getAttribute("data-price");
    let productPiece = selectedOption.getAttribute("data-piece");

    if (productPrice && productPiece) {
        let productQuantity = document.getElementById("Cantidad");

        productQuantity.value = 1;
        document.getElementById("Total").value = productPrice;
        document.getElementById("Precio").value = productPrice;

        productQuantity.removeAttribute("readonly");
        document.getElementById("quantityAvailable").innerText = "Cantidad disponible: " + productPiece;
        productQuantity.setAttribute("max", productPiece);
    }
}

calculateTotalPrice = function () {
    let productQuantity = document.getElementById("Cantidad").value;
    let productID = document.getElementById("ID_Product").value;

    if (productQuantity > 0 && productID) {
        let productPrice = document.getElementById("Precio").value;
        productPrice = parseFloat(productPrice);
        let totalPrice = productPrice * productQuantity;
        document.getElementById("Total").value = totalPrice.toFixed(2);
    }
}

calculateTotalCost = function () {
    let productQuantity = document.getElementById("Cantidad").value;
    let productCost = document.getElementById("CostoUnidad").value;

    if (productQuantity > 0 & productCost > 0) {
        productCost = parseFloat(productCost);
        let totalCost = productCost * productQuantity;
        document.getElementById("CostoTotal").value = totalCost.toFixed(2);
    } else {
        document.getElementById("CostoTotal").value = 0;
    }
}

deleteProductSale = function (Id) {
    let row = Id.parentNode.parentNode;
    let tableProductSales = document.getElementById("salesProductsTable");
    let productSelect = document.querySelector("#ID_Product");
    let selectedProductOption = productSelect.selectedOptions[0]; //el option seleccionado de select
    let allSelectOptions = productSelect.children; //todos los option del select

    let TotalSale = document.getElementById("totalProductSales");

    let productName = row.children[1].innerText;
    let productQuantitySale = row.children[2].innerText;
    let totalProductSale = row.children[4].innerText;

    let newTotalSale = 0;
    let productQuantity = selectedProductOption.getAttribute("data-piece");
    let newTotalQuantity = 0;
    let inputQuantity = document.getElementById("Cantidad");
    let price = undefined;
    const allProductNames = [];
    let productIndexOption = 0;
    let productUpdate = undefined;
    let noSelectedProductQuantity = undefined
    // Variables correctas

    totalProductSale = totalProductSale.replace("$", ""); //cambiar el $ del total del producto vendido
    TotalSale = TotalSale.innerText; // obtener valor de la venta total 
    TotalSale = TotalSale.replace("$", ""); //cambiar el $ del total vendido

    newTotalSale = parseFloat(TotalSale) - parseFloat(totalProductSale); // Restar del total general el total del producto a eliminar
    tableProductSales.deleteRow(row.rowIndex); //Elimina la fila 
    document.getElementById("totalProductSales").innerText = "$" + newTotalSale; //asigna el nuevo total al elemento

    newTotalQuantity = parseInt(productQuantity) + parseInt(productQuantitySale); //Suma a la cantidad total del producto la cantidad vendida eliminada

    for (let index = 0; index < allSelectOptions.length; index++) {
        allProductNames.push(allSelectOptions[index].innerText);
    }

    if (selectedProductOption.innerText == productName) {
        selectedProductOption.setAttribute("data-piece", newTotalQuantity);
        price = selectedProductOption.getAttribute("data-price");
        inputQuantity.value = 1;
        inputQuantity.setAttribute("max", newTotalQuantity);
        document.getElementById("Total").value = price;
        document.getElementById("Precio").value = price;
        document.getElementById("quantityAvailable").innerText = "Cantidad disponible: " + newTotalQuantity;
        console.log("Se cumplio la primera condicion");

    } else if (selectedProductOption.innerText == productName + " (No disponible)") {
        price = selectedProductOption.getAttribute("data-price");
        inputQuantity.value = 1;
        inputQuantity.setAttribute("max", newTotalQuantity);
        document.getElementById("Total").value = price;
        document.getElementById("Precio").value = price;
        inputQuantity.removeAttribute("readonly");
        selectedProductOption.innerText = productName;
        selectedProductOption.setAttribute("data-piece", newTotalQuantity);
        selectedProductOption.removeAttribute("disabled");
        document.getElementById("quantityAvailable").innerText = "Cantidad disponible: " + newTotalQuantity;
        console.log("Se cumplio la segunda condicion");

    } else {

        if (allProductNames.indexOf(productName) != -1) {
            productIndexOption = allProductNames.indexOf(productName);
            productUpdate = allSelectOptions[productIndexOption];

            noSelectedProductQuantity = productUpdate.getAttribute("data-piece");
            newTotalQuantity = parseInt(noSelectedProductQuantity) + parseInt(productQuantitySale);
            productUpdate.setAttribute("data-piece", newTotalQuantity);

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
