function loadProfit() {

    let start = document.getElementById("start_date").value;
    let end = document.getElementById("end_date").value;

    let url = "/api/profit-loss";

    if (start && end) {
        url += `?start_date=${start}&end_date=${end}`;
    }

    fetch(url)
    .then(res => res.json())
    .then(data => {

        document.getElementById("sales").innerText = data.total_sales;
        document.getElementById("purchase").innerText = data.total_purchase;
        document.getElementById("expenses").innerText = data.total_expenses;
        document.getElementById("sale_return").innerText = data.total_sale_return;
        document.getElementById("purchase_return").innerText = data.total_purchase_return;
        document.getElementById("net_profit").innerText = data.net_profit;

        if (data.net_profit < 0) {
            document.querySelector(".profit").style.background = "#f8d7da";
        } else {
            document.querySelector(".profit").style.background = "#d4edda";
        }

    });
}

window.onload = loadProfit;