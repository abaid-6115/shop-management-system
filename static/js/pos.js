function addRow() {
    let table = document.querySelector("#itemsTable tbody");
    let row = table.insertRow();

    row.innerHTML = `
        <td><input type="text"></td>
        <td><input type="number" value="1" oninput="calculate()"></td>
        <td><input type="number" value="0" oninput="calculate()"></td>
        <td class="rowTotal">0.00</td>
        <td><button onclick="removeRow(this)">X</button></td>
    `;
}

function removeRow(btn) {
    btn.parentElement.parentElement.remove();
    calculate();
}

function calculate() {
    let rows = document.querySelectorAll("#itemsTable tbody tr");
    let subtotal = 0;

    rows.forEach(row => {
        let qty = parseFloat(row.cells[1].querySelector("input").value) || 0;
        let price = parseFloat(row.cells[2].querySelector("input").value) || 0;
        let total = qty * price;

        row.querySelector(".rowTotal").innerText = total.toFixed(2);
        subtotal += total;
    });

    document.getElementById("subtotal").innerText = subtotal.toFixed(2);

    let gstPercent = parseFloat(document.getElementById("gst").value) || 0;
    let gstAmount = subtotal * gstPercent / 100;
    document.getElementById("gstAmount").innerText = gstAmount.toFixed(2);

    let discount = parseFloat(document.getElementById("discount").value) || 0;

    let grandTotal = subtotal + gstAmount - discount;
    document.getElementById("grandTotal").innerText = grandTotal.toFixed(2);

    let paid = parseFloat(document.getElementById("paidAmount").value) || 0;
    let change = paid - grandTotal;
    document.getElementById("change").innerText = change.toFixed(2);
}

function saveSale() {

    calculate();

    let rows = document.querySelectorAll("#itemsTable tbody tr");
    let items = [];

    rows.forEach(row => {
        items.push({
            name: row.cells[0].querySelector("input").value,
            qty: row.cells[1].querySelector("input").value,
            price: row.cells[2].querySelector("input").value,
            total: row.querySelector(".rowTotal").innerText
        });
    });

    fetch("/save_pos", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            customer_name: document.getElementById("customerName").value,
            customer_phone: document.getElementById("customerPhone").value,
            subtotal: document.getElementById("subtotal").innerText,
            gst_percentage: document.getElementById("gst").value,
            gst_amount: document.getElementById("gstAmount").innerText,
            discount: document.getElementById("discount").value,
            grand_total: document.getElementById("grandTotal").innerText,
            payment_method: document.getElementById("paymentMethod").value,
            paid_amount: document.getElementById("paidAmount").value,
            change: document.getElementById("change").innerText,
            items: items
        })
    })
    .then(res => res.json())
    .then(data => {
        alert("Sale Saved Successfully!");
        location.reload();
    });
}

function printInvoice() {
    window.print();
}

function goBack() {
    window.location.href = "/dashboard";
}
