$(document).ready(function () {
    const BELT = $(".belt");

    //////////////////////////////////////////////

    function loadAndAnimateImage() {
        fetch('/api/images', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.encoded_image) {
                    const $img = $(`<img src="${data.encoded_image}" />`);
                    BELT.append($img);
                    animateImage($img);
                } else {
                    console.log("No images available.");
                }
            })
            .catch(err => console.error("Error loading image:", err));
    }

    //////////////////////////////////////////////

    function animateImage($img) {
        $img.css({
            position: "absolute",
            right: "-800px", // 이미지가 화면 오른쪽 바깥에서 시작
            transition: "right 10s linear" // 10초 동안 이동
        });

        // Start animation
        setTimeout(() => {
            $img.css("right", "100%"); // 화면 왼쪽으로 이동
        }, 100);

        // Remove image after animation
        setTimeout(() => {
            $img.remove(); // 애니메이션 종료 후 이미지 제거
        }, 10000); // 10초 후 제거
    }


    //////////////////////////////////////////////

    function continuouslyLoadImages() {
        setInterval(() => {
            loadAndAnimateImage(); // 주기적으로 이미지를 로드하고 애니메이션 시작
        }, 5000); // 5초마다 새로운 이미지 로드
    }

    continuouslyLoadImages();

    detectPosition();

    //////////////////////////////////////////////

    function detectPosition() {
        const detectionZone = document.querySelector('.detection-zone');
        const zoneLeft = detectionZone.getBoundingClientRect().left;
    
        requestAnimationFrame(() => {
            $('.belt img').each(function () {
                const $img = $(this);
                const imgRect = $img[0].getBoundingClientRect();
                const imgCenter = imgRect.left + imgRect.width / 2;
    
                if (Math.abs(imgCenter - zoneLeft) < 5 && !$img.data('processed')) {
                    processImage($img);
                    $img.data('processed', true);
                }
            });
            detectPosition();
        });
    }

    //////////////////////////////////////////////

    async function processImage($img) {
        try {
            const base64Data = $img.attr('src').split('base64,')[1];
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
    
            $img.attr('src', `data:image/png;base64,${result.annotated_image}`);
    
            if (result.predictions.some((p) => p.label === 'Defect')) {
                Swal.fire({
                    icon: "warning",
                    title: "불량품 감지!",
                    text: "ㅇㅇㅇ",
                    confirmButtonText: "확인",
                    timer: 3000,
                    timerProgressBar: true,
                    customClass: {
                        timerProgressBar: "timer-bar",
                    }
                });
            }
        } catch (error) {
            console.error('처리 실패:', error);
        }
    }

    //////////////////////////////////////////////
});
