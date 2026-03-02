let currentSale = null;

function searchSale() {
    const invoice = document.getElementById("invoice").value;

    fetch("/search_sale", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ invoice: invoice })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "not_found") {
            alert("Invoice not found");
            return;
        }

        currentSale = data;
        displaySale(data);
    });
}

function displaySale(data) {
    const tbody = document.querySelector("#return_table tbody");
    const customerDiv = document.getElementById("customer_info");

    customerDiv.innerHTML = `
        <h4>Customer: ${data.sale.customer_name}</h4>
        <h4>Phone: ${data.sale.customer_phone}</h4>
    `;

    tbody.innerHTML = "";

    data.items.forEach(item => {
        const sold = parseFloat(item.quantity);
        const returned = parseFloat(item.returned_quantity);
        const remaining = sold - returned;

        tbody.innerHTML += `
            <tr>
                <td>${item.stock_products.product_name}</td>
                <td>${sold}</td>
                <td>${returned}</td>
                <td>${remaining}</td>
                <td>
                    <input type="number" min="0" max="${remaining}" value="0"
                        data-sale-item="${item.id}"
                        data-stock="${item.stock_id}"
                        data-price="${item.price}"
                        onchange="calculateTotal()">
                </td>
                <td>${item.price}</td>
                <td class="item_total">0</td>
            </tr>
        `;
    });
}

function calculateTotal() {
    let total = 0;

    document.querySelectorAll("#return_table tbody tr").forEach(row => {
        const input = row.querySelector("input");
        const qty = parseFloat(input.value) || 0;
        const price = parseFloat(input.dataset.price);

        const itemTotal = qty * price;
        row.querySelector(".item_total").innerText = itemTotal;

        total += itemTotal;
    });

    document.getElementById("total_refund").innerText = total;
}

function completeReturn() {
    let items = [];

    document.querySelectorAll("#return_table tbody tr").forEach(row => {
        const input = row.querySelector("input");
        const qty = parseFloat(input.value) || 0;

        if (qty > 0) {
            items.push({
                sale_item_id: input.dataset.saleItem,
                stock_id: input.dataset.stock,
                qty: qty,
                price: input.dataset.price
            });
        }
    });

    fetch("/complete_return", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            sale_id: currentSale.sale.id,
            items: items,
            reason: document.getElementById("reason").value,
            refund_method: document.getElementById("refund_method").value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            alert("Return Completed Successfully");
            location.reload();
        } else {
            alert(data.message);
        }
    });
}