$(document).ready(function() {
        $("#generate-form").submit(function(e) {
            e.preventDefault();
            let text = $("#text").val();
            let errorMessage = $("#error-message");
            let errorSound = $("#error-sound")[0];
    
            if (text.length < 15) {
                $("#text").addClass('error');
                errorMessage.text("寄件編號必須至少15個字符").show();
                errorSound.play();
                return;
            } else {
                $("#text").removeClass('error');
                errorMessage.hide();
            }
    
            $.post("/generate_qr", { text: text }, function(response) {
                if (response.status === 'success') {
                    $("#text").val('');  // 清空輸入欄
                    updateTable(response.qr_data);
                } else {
                    errorMessage.text(response.message).show();
                    errorSound.play();
                }
            });
        });
    
        $("#clear-all").click(function() {
            $.post("/clear_all", function(response) {
                if (response.status === 'success') {
                    updateTable([]);
                }
            });
        });
    });
    
    function updateTable(qr_data) {
        let tableBody = $("#qr-code-table");
        tableBody.empty();
        qr_data.forEach((data, index) => {
            let row = `<tr>
                <td>${index + 1}</td>
                <td>${data.text}</td>
                <td><img src="${data.qr_code}" alt="QR Code"></td>
                <td>${data.timestamp}</td>
            </tr>`;
            tableBody.append(row);
        });
    }
    
    function generateExcel() {
        window.location.href = '/generate_excel';
    }
    
    function clearAll() {
        fetch('/clear_all', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateTable([]);
                }
            });
    }