let cart = [];

function addToCart() {

    let input = document.getElementById("productSearch");
    let qty = parseFloat(document.getElementById("quantity").value);

    let option = [...document.querySelectorAll("#productList option")]
        .find(o => o.value === input.value);

    if (!option) {
        alert("Select valid product");
        return;
    }

    let stockId = option.dataset.id;
    let price = parseFloat(option.dataset.price);
    let available = parseFloat(option.dataset.qty);

    if (qty > available) {
        alert("Not enough stock available!");
        return;
    }

    let total = qty * price;

    cart.push({
        stock_id: stockId,
        name: input.value,
        qty: qty,
        price: price,
        total: total
    });

    renderCart();
}

function renderCart() {

    let tbody = document.querySelector("#cartTable tbody");
    tbody.innerHTML = "";

    let subtotal = 0;

    cart.forEach((item, index) => {
        subtotal += item.total;

        tbody.innerHTML += `
            <tr>
                <td>${item.name}</td>
                <td>${item.qty}</td>
                <td>${item.price}</td>
                <td>${item.total}</td>
                <td><button onclick="removeItem(${index})">X</button></td>
            </tr>
        `;
    });

    document.getElementById("subtotal").innerText = subtotal.toFixed(2);

    calculateTotal();
}

function removeItem(index) {
    cart.splice(index, 1);
    renderCart();
}

function calculateTotal() {

    let subtotal = parseFloat(document.getElementById("subtotal").innerText);
    let gst = parseFloat(document.getElementById("gst").value);
    let discount = parseFloat(document.getElementById("discount").value);
    let paid = parseFloat(document.getElementById("paidAmount").value);

    let gstAmount = subtotal * gst / 100;
    let grandTotal = subtotal + gstAmount - discount;
    let change = paid - grandTotal;

    document.getElementById("grandTotal").innerText = grandTotal.toFixed(2);
    document.getElementById("change").innerText = change.toFixed(2);
}

document.getElementById("gst").addEventListener("input", calculateTotal);
document.getElementById("discount").addEventListener("input", calculateTotal);
document.getElementById("paidAmount").addEventListener("input", calculateTotal);

function completeSale() {

    fetch("/complete_sale", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            customer_name: document.getElementById("customerName").value,
            customer_phone: document.getElementById("customerPhone").value,
            subtotal: document.getElementById("subtotal").innerText,
            gst_percentage: document.getElementById("gst").value,
            gst_amount: 0,
            discount: document.getElementById("discount").value,
            grand_total: document.getElementById("grandTotal").innerText,
            payment_method: document.getElementById("paymentMethod").value,
            paid_amount: document.getElementById("paidAmount").value,
            change: document.getElementById("change").innerText,
            items: cart
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            alert("Sale Completed!");
            location.reload();
        } else {
            alert("Error completing sale");
        }
    });
}