let items = [];

function addProduct() {
    let product = document.getElementById("product").value;
    let category = document.getElementById("category").value;
    let unit = document.getElementById("unit").value;
    let quantity = parseFloat(document.getElementById("quantity").value);
    let cost = parseFloat(document.getElementById("cost").value);
    let sell = parseFloat(document.getElementById("sell").value);

    let total = quantity * cost;

    let item = {product, category, unit, quantity, cost, sell, total};
    items.push(item);

    renderTable();
    calculateTotals();
}

function renderTable() {
    let tbody = document.querySelector("#productTable tbody");
    tbody.innerHTML = "";

    items.forEach((item, index) => {
        let row = `
        <tr>
        <td>${item.product}</td>
        <td>${item.category}</td>
        <td>${item.unit}</td>
        <td>${item.quantity}</td>
        <td>${item.cost}</td>
        <td>${item.sell}</td>
        <td>${item.total}</td>
        <td>
        <button onclick="deleteItem(${index})">Delete</button>
        </td>
        </tr>`;
        tbody.innerHTML += row;
    });
}

function deleteItem(index) {
    items.splice(index, 1);
    renderTable();
    calculateTotals();
}

function calculateTotals() {
    let subtotal = items.reduce((sum, item) => sum + item.total, 0);
    document.getElementById("subtotal").innerText = subtotal;

    let gst = parseFloat(document.getElementById("gst").value) || 0;
    let tax = subtotal * gst / 100;
    document.getElementById("tax_amount").innerText = tax;

    let discount = parseFloat(document.getElementById("discount").value) || 0;

    let grand = subtotal + tax - discount;
    document.getElementById("grand_total").innerText = grand;

    let paid = parseFloat(document.getElementById("paid").value) || 0;
    let balance = grand - paid;

    document.getElementById("balance").innerText = balance;
}
function completePurchase() {
    fetch("/complete_purchase", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            supplier_name: document.getElementById("supplier_name").value,
            phone: document.getElementById("phone").value,
            subtotal: document.getElementById("subtotal").innerText,
            gst: document.getElementById("gst").value,
            tax_amount: document.getElementById("tax_amount").innerText,
            discount: document.getElementById("discount").value,
            grand_total: document.getElementById("grand_total").innerText,
            paid: document.getElementById("paid").value,
            balance: document.getElementById("balance").innerText,
            payment_method: document.getElementById("payment_method").value,
            items: items
        })
    })
    .then(res => res.json())
    .then(data => {

        if (data.status === "success") {
            alert("Purchase Completed Successfully!\nInvoice: " + data.invoice);
            location.reload();
        } else {
            alert("Error saving purchase.");
        }

    });
}