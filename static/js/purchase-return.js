let currentData = null;

function searchInvoice(){

    let invoice = document.getElementById("invoiceInput").value.trim();

    if(invoice === ""){
        alert("Please enter invoice number");
        return;
    }

    fetch("/search_purchase_invoice",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({invoice:invoice})
    })
    .then(res=>res.json())
    .then(data=>{
        if(data.error){
            alert(data.error);
            return;
        }

        currentData = data;
        renderData();
    });
}

function renderData(){

    document.getElementById("supplierDetails").innerHTML =
        `<h3>Supplier: ${currentData.supplier.supplier_name} 
        (${currentData.supplier.phone})</h3>`;

    let tbody = document.querySelector("#itemsTable tbody");
    tbody.innerHTML = "";

    currentData.items.forEach(item=>{

        let returned = item.returned_quantity || 0;
        let maxQty = item.quantity - returned;

        tbody.innerHTML += `
        <tr>
            <td>${item.product_name}</td>
            <td>${item.quantity}</td>
            <td>${returned}</td>
            <td>${item.stock_quantity}</td>
            <td>
                <input type="number" 
                       min="0" 
                       max="${maxQty}" 
                       value="0"
                       data-id="${item.id}"
                       data-cost="${item.cost_price}"
                       oninput="calculateTotals()">
            </td>
            <td>${item.cost_price}</td>
            <td class="rowTotal">0</td>
        </tr>`;
    });

    calculateTotals();
}

function calculateTotals(){

    let rows = document.querySelectorAll("#itemsTable tbody tr");
    let subtotal = 0;

    rows.forEach(row=>{

        let qtyInput = row.querySelector("input");
        let qty = parseFloat(qtyInput.value) || 0;
        let cost = parseFloat(qtyInput.dataset.cost);

        let total = qty * cost;

        row.querySelector(".rowTotal").innerText = total.toFixed(2);

        subtotal += total;
    });

    let gstPercent = parseFloat(document.getElementById("gst").value) || 0;
    let discount = parseFloat(document.getElementById("discount").value) || 0;

    let gstAmount = subtotal * (gstPercent / 100);
    let grandTotal = subtotal + gstAmount - discount;

    document.getElementById("grandTotal").innerHTML =
        `Subtotal: ${subtotal.toFixed(2)} <br>
         GST: ${gstAmount.toFixed(2)} <br>
         Discount: ${discount.toFixed(2)} <br>
         <strong>Grand Total: ${grandTotal.toFixed(2)}</strong>`;
}

function saveReturn(){

    let rows = document.querySelectorAll("#itemsTable tbody tr");
    let items = [];

    rows.forEach(row=>{

        let input = row.querySelector("input");
        let qty = parseFloat(input.value);

        if(qty > 0){

            let id = input.dataset.id;
            let item = currentData.items.find(i=>i.id==id);

            items.push({
                id:item.id,
                product_name:item.product_name,
                cost_price:item.cost_price,
                return_qty:qty,
                returned_quantity:item.returned_quantity || 0
            });
        }
    });

    if(items.length === 0){
        alert("Please enter return quantity");
        return;
    }

    fetch("/save_purchase_return",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            purchase_id:currentData.purchase.id,
            supplier_id:currentData.purchase.supplier_id,
            items:items,
            refund_method:document.getElementById("refundMethod").value,
            tax_percentage:document.getElementById("gst").value,
            discount:document.getElementById("discount").value
        })
    })
    .then(res => {
    if(!res.ok){
        return res.text().then(text => { throw new Error(text); });
    }
    return res.json();
        })
        .then(data=>{
            alert("Return Saved. Invoice: "+data.invoice);
            location.reload();
        })
        .catch(error=>{
            console.error("Server Error:", error);
            alert("Server Error. Check terminal.");
        });
    }
