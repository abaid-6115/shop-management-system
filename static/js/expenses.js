document.addEventListener("DOMContentLoaded", loadExpenses);

function addExpense(){

    fetch("/add_expense",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            expense_date:document.getElementById("expense_date").value,
            category:document.getElementById("category").value,
            description:document.getElementById("description").value,
            amount:document.getElementById("amount").value,
            payment_method:document.getElementById("payment_method").value,
            reference:document.getElementById("reference").value
        })
    })
    .then(res=>res.json())
    .then(data=>{
        if(data.success){
            alert("Expense Added Successfully");
            loadExpenses();
        }else{
            alert(data.error);
        }
    });
}


function loadExpenses(){

    fetch("/get_expenses",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            start_date:document.getElementById("start_date").value,
            end_date:document.getElementById("end_date").value,
            category:document.getElementById("filter_category").value,
            payment_method:document.getElementById("filter_payment").value
        })
    })
    .then(res=>res.json())
    .then(data=>{

        let table = document.getElementById("expenseTable");
        table.innerHTML = "";

        data.expenses.forEach(e=>{
            table.innerHTML += `
            <tr>
            <td>${e.expense_date}</td>
            <td>${e.category}</td>
            <td>${e.description || ''}</td>
            <td>${e.amount}</td>
            <td>${e.payment_method}</td>
            <td>${e.reference || ''}</td>
            <td><button onclick="deleteExpense(${e.id})">Delete</button></td>
            </tr>`;
        });

        document.getElementById("totalExpense").innerText = data.total;
    });
}


function deleteExpense(id){

    if(!confirm("Delete this expense?")) return;

    fetch("/delete_expense/"+id,{
        method:"DELETE"
    })
    .then(res=>res.json())
    .then(data=>{
        if(data.success){
            loadExpenses();
        }
    });
}
