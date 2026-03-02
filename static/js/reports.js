let currentType = "";

function loadData(type) {
    currentType = type;

    fetch(`/get_report_data/${type}`)
        .then(res => res.json())
        .then(data => {

            const table = document.getElementById("reportTable");
            table.innerHTML = "";

            data.forEach(item => {

                table.innerHTML += `
                    <tr>
                        <td>${item.invoice_number}</td>
                        <td>${item.total_amount}</td>
                        <td>${item.created_at || ''}</td>
                        <td>
                            <a href="/print_invoice/${type}/${item.id}" target="_blank">
                                Print
                            </a>
                        </td>
                        <td>
                            <button class="delete"
                                onclick="deleteRecord(${item.id})">
                                Delete
                            </button>
                        </td>
                    </tr>
                `;
            });
        });
}

function deleteRecord(id) {

    if (!confirm("Are you sure?")) return;

    fetch(`/delete_record/${currentType}/${id}`, {
        method: "DELETE"
    })
    .then(res => res.json())
    .then(() => loadData(currentType));
}
