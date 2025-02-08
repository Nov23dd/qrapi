$(document).ready(function() {
    const username = "{{ username }}";  // 確保用戶名正確獲取

    // 處理表單提交
    $("#generate-form").submit(function(e) {
        e.preventDefault();
        let text = $("#text").val();
        let errorMessage = $("#error-message");
        let successMessage = $("#success-message");
        let errorSound = $("#error-sound")[0];
        let successSound = $("#success-sound")[0];

        // 驗證文本長度
        if (text.length !== 15) {
            showErrorMessage("寄件編號必須至少15個字符");
            errorSound.play();
            $("#text").val('');  // 清空輸入欄
            return;
        } 

        // 發送 POST 請求
        $.post(`/generate_qr/${username}`, { text: text }, function(response) {
            if (response.status === 'success') {
                $("#text").val('');  // 清空輸入欄
                showSuccessMessage("刷取成功");
                successSound.play();
                updateTable(response.qr_data);
                updateCounter(response.counter);
            } else {
                showErrorMessage(response.message);
                errorSound.play();
            }
        });
    });

    // 處理清除全部請求
    $("#clear-all").click(function() {
        $.post(`/clear_all/${username}`, function(response) {
            if (response.status === 'success') {
                updateTable([]);
                updateCounter(0);
            }
        });
    });

    // 處理匯出 PDF 功能
    $("#export-pdf").click(function() {
        $.post(`/export_pdf/${username}`, function(response) {
            if (response.status === 'success') {
                var link = document.createElement('a');
                link.href = 'data:application/pdf;base64,' + response.pdf;
                link.download = response.file_name;
                link.click();
            } else {
                alert('Error: ' + response.message);
            }
        });
    });
});

// 顯示錯誤消息
function showErrorMessage(message) {
    let errorMessage = $("#error-message");
    errorMessage.text(message).show();
    $("#text").addClass('error');
    setTimeout(function() {
        errorMessage.hide();
        $("#text").removeClass('error');
    }, 3000);
}

// 顯示成功消息
function showSuccessMessage(message) {
    let successMessage = $("#success-message");
    successMessage.text(message).show();
    setTimeout(function() {
        successMessage.hide();
    }, 2000);
}

// 更新表格
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

// 更新計數器
function updateCounter(counter) {
    $("#counter-display").text("目前處理的件數：" + counter);
}