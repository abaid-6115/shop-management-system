function addProduct() {

    fetch("/add_product", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            product_name: document.getElementById("productName").value,
            category: document.getElementById("category").value,
            unit_type: document.getElementById("unitType").value,
            cost_price: document.getElementById("costPrice").value,
            selling_price: document.getElementById("sellingPrice").value,
            quantity: document.getElementById("quantity").value
        })
    })
    .then(res => res.json())
    .then(data => {
        alert("Product Added Successfully!");
        location.reload();
    });
}

function updateProduct(id) {

    fetch("/update_product/" + id, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            cost_price: document.getElementById("cost-" + id).value,
            selling_price: document.getElementById("sell-" + id).value,
            quantity: document.getElementById("qty-" + id).value
        })
    })
    .then(res => res.json())
    .then(data => {
        alert("Product Updated Successfully!");
        location.reload();
    });
}

function goBack() {
    window.location.href = "/dashboard";
}