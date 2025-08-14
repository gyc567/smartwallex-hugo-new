// 点赞功能
const LIKES_STORAGE_KEY = 'blog_likes';

// 初始化点赞功能
document.addEventListener('DOMContentLoaded', function() {
    initializeLikes();
});

// 初始化所有点赞按钮
function initializeLikes() {
    const likeButtons = document.querySelectorAll('.post-likes');
    
    likeButtons.forEach(button => {
        const postId = button.getAttribute('data-post');
        const likeCount = getLikeCount(postId);
        const isLiked = isPostLiked(postId);
        
        updateLikeDisplay(button, likeCount, isLiked);
    });
}

// 切换点赞状态
function toggleLike(postId) {
    const likes = getLikes();
    const currentCount = likes[postId] ? likes[postId].count : 0;
    const isLiked = likes[postId] ? likes[postId].liked : false;
    
    if (isLiked) {
        // 取消点赞
        likes[postId] = {
            count: Math.max(0, currentCount - 1),
            liked: false
        };
    } else {
        // 点赞
        likes[postId] = {
            count: currentCount + 1,
            liked: true
        };
    }
    
    // 保存到本地存储
    localStorage.setItem(LIKES_STORAGE_KEY, JSON.stringify(likes));
    
    // 更新显示
    const likeButton = document.querySelector(`[data-post="${postId}"]`);
    if (likeButton) {
        updateLikeDisplay(likeButton, likes[postId].count, likes[postId].liked);
    }
    
    // 添加动画效果
    animateLike(likeButton);
}

// 获取所有点赞数据
function getLikes() {
    const stored = localStorage.getItem(LIKES_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
}

// 获取特定文章的点赞数
function getLikeCount(postId) {
    const likes = getLikes();
    return likes[postId] ? likes[postId].count : 0;
}

// 检查文章是否被当前用户点赞
function isPostLiked(postId) {
    const likes = getLikes();
    return likes[postId] ? likes[postId].liked : false;
}

// 更新点赞按钮显示
function updateLikeDisplay(likeButton, count, isLiked) {
    const countElement = likeButton.querySelector('.like-count');
    const btnElement = likeButton.querySelector('.like-btn');
    
    if (countElement) {
        countElement.textContent = count;
    }
    
    if (btnElement) {
        if (isLiked) {
            btnElement.classList.add('liked');
            btnElement.style.color = '#e74c3c';
        } else {
            btnElement.classList.remove('liked');
            btnElement.style.color = '';
        }
    }
}

// 点赞动画效果
function animateLike(likeButton) {
    const btnElement = likeButton.querySelector('.like-btn');
    if (btnElement) {
        btnElement.style.transform = 'scale(1.2)';
        setTimeout(() => {
            btnElement.style.transform = 'scale(1)';
        }, 200);
        
        // 创建飞出的心形动画
        createHeartAnimation(btnElement);
    }
}

// 创建心形飞出动画
function createHeartAnimation(element) {
    const heart = document.createElement('span');
    heart.innerHTML = '❤️';
    heart.style.position = 'absolute';
    heart.style.fontSize = '1.5rem';
    heart.style.pointerEvents = 'none';
    heart.style.zIndex = '1000';
    
    const rect = element.getBoundingClientRect();
    heart.style.left = rect.left + 'px';
    heart.style.top = rect.top + 'px';
    
    document.body.appendChild(heart);
    
    // 动画
    let opacity = 1;
    let translateY = 0;
    
    const animate = () => {
        opacity -= 0.02;
        translateY -= 2;
        
        heart.style.opacity = opacity;
        heart.style.transform = `translateY(${translateY}px)`;
        
        if (opacity > 0) {
            requestAnimationFrame(animate);
        } else {
            document.body.removeChild(heart);
        }
    };
    
    requestAnimationFrame(animate);
}

// 导出点赞数据（用于统计）
function exportLikesData() {
    const likes = getLikes();
    console.log('点赞数据:', likes);
    return likes;
}