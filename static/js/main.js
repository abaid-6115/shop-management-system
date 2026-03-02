// Simple confirmation for future delete actions

function confirmDelete() {
    return confirm("Are you sure you want to delete?");
}

// Future: Search filter
function searchTable(inputId, tableId) {
    let input = document.getElementById(inputId);
    let filter = input.value.toUpperCase();
    let table = document.getElementById(tableId);
    let tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        let td = tr[i].getElementsByTagName("td")[0];
        if (td) {
            let txtValue = td.textContent || td.innerText;
            tr[i].style.display =
                txtValue.toUpperCase().indexOf(filter) > -1 ? "" : "none";
        }
    }
}
