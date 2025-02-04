$(document).ready(function () {
    const BELT = $(".belt");
    let isProcessing = false;

    // 랜덤 이미지 로드 및 컨베이어 벨트 시작
    fetch('/api/list-images')
        .then(res => res.json())
        .then(images => {
            images.forEach(base64Data => {
                BELT.append(`<img src="${base64Data}" class="belt-img">`);
            });
            startConveyor();
        });

    function startConveyor() {
        BELT.css('animation', 'moveBelt 30s linear infinite');
        detectPosition();
    }

    function detectPosition() {
        const detectionZone = document.querySelector('.detection-zone');
        const zoneLeft = detectionZone.getBoundingClientRect().left;
    
        requestAnimationFrame(() => {
            // jQuery의 .each()를 사용하여 순회
            $('.belt img').each(function () {
                const $img = $(this); // DOM 객체를 jQuery로 래핑
                const imgRect = $img[0].getBoundingClientRect(); // DOM 메서드 호출
                const imgCenter = imgRect.left + imgRect.width / 2;
    
                // 이미지가 판별 구역에 도달했는지 확인
                if (Math.abs(imgCenter - zoneLeft) < 5 && !$img.data('processed')) {
                    processImage($img); // $img는 이제 jQuery 객체
                    $img.data('processed', true); // 중복 처리 방지
                }
            });
    
            detectPosition(); // 지속적으로 감시
        });
    }
    
    async function processImage($img) {
        try {
            const base64Data = $img.attr('src').split('base64,')[1]; // .attr() 사용 가능
            const res = await fetch('/api/pipe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: base64Data }),
            });
    
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            
            const result = await res.json();
    
            if (!result.annotated_image || !result.predictions) {
                throw new Error('Invalid server response');
            }
    
            // 응답 이미지 업데이트
            $img.attr('src', `data:image/png;base64,${result.annotated_image}`);
    
            // Defect 감지
            if (result.predictions.some((p) => p.label === 'Defect')) {
                handleDefect($img);
            }
        } catch (error) {
            console.error('처리 실패:', error);
        }
    }

    function handleDefect($img) {
        const belt = $(".belt"); // 컨베이어 벨트 요소
    
        // 애니메이션 일시 정지
        belt.css("animation-play-state", "paused");
    
        // SweetAlert2 경고창 표시
        Swal.fire({
            icon: "warning",
            title: "불량품 감지!",
            text: "컨베이어 벨트를 멈춥니다.",
            confirmButtonText: "확인",
            timer: 3000,
            timerProgressBar: true,
            customClass: {
                timerProgressBar: "timer-bar",
            },
        }).then(() => {
            // 경고창 닫힌 후 애니메이션 재개
            resumeConveyor(belt);
        });
    }
    
    function resumeConveyor(belt) {
        belt.css("animation-play-state", "running");
    }    

});
