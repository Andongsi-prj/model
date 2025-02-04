$(document).ready(function() {
    loadData();
});

function loadData() {
    $.ajax({
        url: '/api/data/data',
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            // 파이차트 이미지 표시
            const chartImage = document.getElementById('chartImage');
            chartImage.src = 'data:image/png;base64,' + response.chart;
            // $('.chart-container').html(chartImage);
            
            // 통계 데이터 업데이트
            $('#totalCount').text(response.total.toLocaleString() + '개');
            $('#normalCount').text(response.normal.toLocaleString() + '개');
            $('#defectCount').text(response.defect.toLocaleString() + '개');
        },
        error: function(error) {
            console.error('Error:', error);
            alert('데이터 로드 중 오류가 발생했습니다.');
        }
    });
}