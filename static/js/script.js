$(document).ready(function() {
    const username = $("#username").val();

    // 排序邏輯
    var items = $('#qr-code-table tr');
    $('#qr-code-table').append(items.get().reverse());

    $("#generate-form").submit(function(e) {
        e.preventDefault();
        let text = $("#text").val();
        let errorMessage = $("#error-message");
        let successMessage = $("#success-message");
        let errorSound = $("#error-sound")[0];
        let successSound = $("#success-sound")[0];

        if (text.length < 15) {
            $("#text").addClass('error');
            errorMessage.text("寄件編號必須至少15個字符").show();
            errorSound.play();
            $("#text").val('');  // 清空輸入欄
            return;
        } else {
            $("#text").removeClass('error');
            errorMessage.hide();
        }

        $.post(`/generate_qr/${username}`, { text: text }, function(response) {
            if (response.status === 'success') {
                $("#text").val('');  // 清空輸入欄
                successMessage.text("刷取成功").show();
                successSound.play();
                setTimeout(function() {
                    successMessage.hide();
                }, 2000);  // 2秒後隱藏提示信息
                updateTable(response.qr_data);
                updateCounter(response.counter);
            } else {
                $("#text").val('');  // 清空輸入欄
                errorMessage.text(response.message).show();
                errorSound.play();
            }
        });
    });

    $("#clear-all").click(function() {
        $.post(`/clear_all/${username}`, function(response) {
            if (response.status === 'success') {
                updateTable([]);
                updateCounter(0);
            }
        });
    });

    // 匯出 PDF 的功能
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
    // 將新添加的項目顯示在最下面
    var items = $('#qr-code-table tr');
    $('#qr-code-table').append(items.get().reverse());
}

function updateCounter(counter) {
    $("#counter-display").text("目前處理的件數：" + counter);
}
