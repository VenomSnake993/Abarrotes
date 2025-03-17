confirmActions = function(message) {
    return confirm(message);
}

openUpdateProductWindow = function(button) {
    let url = button.getAttribute("data-url");
    window.open(url, '_blank', ',menubar=0,location=yes,resizable=0,scrollbars=1,status=1,titlebar=1,width=640,height=600');
}

getPriceProduct = function() {
    var selectedProduct = document.getElementById("ID_Product").children;
    id = document.getElementById("ID_Product").value;
    if (id in selectedProduct){
        var price = selectedProduct[id].getAttribute("data-price");
        document.getElementById("Precio").value = price;
        document.getElementById("Cantidad").removeAttribute("readonly");
    }
}

calculateTotalPrice = function(){
    Quantity = document.getElementById("Cantidad").value;
    id = document.getElementById("ID_Product").value;

    if (Quantity > 0 & id !=""){
        price = document.getElementById("Precio").value;
        price = parseFloat(price);
        totalPrice = price * Quantity;
        document.getElementById("Total").value = totalPrice.toFixed(2);
    }
}

calculateTotalCost = function(){
    quantity = document.getElementById("Cantidad").value;
    cost = document.getElementById("CostoUnidad").value;

    if (quantity > 0 & cost > 0){
        cost = parseFloat(cost)
        totalCost = cost * quantity;
        document.getElementById("CostoTotal").value = totalCost.toFixed(2);
    }else {
        document.getElementById("CostoTotal").value = 0
    }
}