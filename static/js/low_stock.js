async function loadLowStock() {

    const search = document.getElementById("search").value;
    const filter = document.getElementById("filter").value;

    const response = await fetch(`/api/low-stock?search=${search}&filter=${filter}`);
    const data = await response.json();

    const table = document.getElementById("stockTable");
    table.innerHTML = "";

    data.forEach(item => {

        let rowClass = "";
        if (item.status === "Low Stock") rowClass = "low";
        if (item.status === "Out of Stock") rowClass = "out";

        table.innerHTML += `
            <tr class="${rowClass}">
                <td>${item.product_name}</td>
                <td>${item.category}</td>
                <td>${item.quantity}</td>
                <td>${item.low_stock_limit}</td>
                <td>${item.status}</td>
                <td>
                    <a href="/purchase">
                        <button>Reorder</button>
                    </a>
                </td>
            </tr>
        `;
    });
}

window.onload = loadLowStock;