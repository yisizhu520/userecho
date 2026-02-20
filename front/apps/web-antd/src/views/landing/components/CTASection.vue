<script lang="ts" setup>
import { ref } from 'vue';

// 表单数据
const formData = ref({
  name: '',
  phone: '',
  company: '',
});

// 表单提交状态
const isSubmitting = ref(false);
const isSubmitted = ref(false);

// 提交表单
const handleSubmit = async () => {
  if (!formData.value.name || !formData.value.phone) {
    alert('请填写姓名和联系方式');
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    // 调用后端 API
    const response = await fetch('/api/v1/app/landing/trial-application', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData.value),
    });
    
    if (response.ok) {
      isSubmitted.value = true;
      // 重置表单
      formData.value = { name: '', phone: '', company: '' };
    } else {
      alert('提交失败，请稍后重试');
    }
  } catch (error) {
    console.error('Submit error:', error);
    alert('网络错误，请稍后重试');
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <section id="contact" class="cta-section">
    <div class="cta-container">
      <!-- Background effects -->
      <div class="cta-bg-gradient"></div>
      <div class="cta-bg-grid"></div>
      <div class="cta-glow cta-glow-1"></div>
      <div class="cta-glow cta-glow-2"></div>

      <div class="cta-content">
        <div class="cta-header">
          <div class="cta-badge">
            <span class="cta-badge-dot"></span>
            <span class="cta-badge-text">🔥 限时福利</span>
          </div>

          <h2 class="cta-title">前 100 名用户免费体验3个月</h2>
          <p class="cta-subtitle">
            已有 16 家团队加入，仅剩 <strong>84</strong> 个名额
          </p>
        </div>

        <div class="cta-main">
          <!-- 左侧：联系表单 -->
          <div class="contact-form-wrapper">
            <h3 class="form-title">留下联系方式，我们会尽快联系您</h3>
            
            <div v-if="!isSubmitted" class="contact-form">
              <div class="form-group">
                <label for="name">姓名 *</label>
                <input 
                  id="name"
                  v-model="formData.name" 
                  type="text" 
                  placeholder="您的姓名"
                  required
                />
              </div>
              
              <div class="form-group">
                <label for="phone">手机/微信 *</label>
                <input 
                  id="phone"
                  v-model="formData.phone" 
                  type="text" 
                  placeholder="手机号或微信号"
                  required
                />
              </div>
              
              <div class="form-group">
                <label for="company">公司/团队</label>
                <input 
                  id="company"
                  v-model="formData.company" 
                  type="text" 
                  placeholder="您的公司或团队名称（选填）"
                />
              </div>
              
              <button 
                class="submit-btn" 
                :disabled="isSubmitting"
                @click="handleSubmit"
              >
                <span v-if="isSubmitting">提交中...</span>
                <span v-else>立即申请免费试用</span>
              </button>
            </div>
            
            <!-- 提交成功提示 -->
            <div v-else class="success-message">
              <div class="success-icon">✓</div>
              <h4>提交成功！</h4>
              <p>我们会在 24 小时内与您联系</p>
            </div>
          </div>

          <!-- 分隔线 -->
          <div class="divider">
            <span>或</span>
          </div>

          <!-- 右侧：微信二维码 -->
          <div class="wechat-wrapper">
            <h3 class="wechat-title">扫码添加微信</h3>
            <div class="qrcode-placeholder">
              <!-- 占位图 - 后续替换为真实二维码 -->
              <div class="qrcode-box">
                <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
                  <rect width="120" height="120" rx="8" fill="currentColor" opacity="0.1"/>
                  <rect x="20" y="20" width="30" height="30" rx="4" fill="currentColor" opacity="0.3"/>
                  <rect x="70" y="20" width="30" height="30" rx="4" fill="currentColor" opacity="0.3"/>
                  <rect x="20" y="70" width="30" height="30" rx="4" fill="currentColor" opacity="0.3"/>
                  <rect x="55" y="55" width="10" height="10" fill="currentColor" opacity="0.5"/>
                  <rect x="70" y="70" width="30" height="30" rx="4" fill="currentColor" opacity="0.2"/>
                </svg>
                <span class="qrcode-hint">微信二维码</span>
              </div>
            </div>
            <p class="wechat-desc">添加客服微信，获取专属服务</p>
          </div>
        </div>

        <div class="cta-features">
          <div class="cta-feature">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>免费体验3个月专业版</span>
          </div>
          <div class="cta-feature">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>1对1专属对接</span>
          </div>
          <div class="cta-feature">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>24小时内响应</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.cta-section {
  position: relative;
  padding: 6rem 2rem;
  overflow: hidden;
}

.cta-container {
  max-width: 900px;
  margin: 0 auto;
  position: relative;
  background: var(--lp-bg-card);
  border: 1px solid var(--lp-border-default);
  border-radius: 32px;
  overflow: hidden;
  backdrop-filter: blur(12px);
}

/* Background effects */
.cta-bg-gradient {
  position: absolute;
  inset: 0;
  background: var(--lp-bg-tertiary);
  opacity: 0.5;
}

.cta-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(var(--lp-border-subtle) 1px, transparent 1px),
    linear-gradient(90deg, var(--lp-border-subtle) 1px, transparent 1px);
  background-size: 40px 40px;
}

.cta-glow {
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
}

.cta-glow-1 {
  top: -200px;
  left: -100px;
  background: rgba(245, 158, 11, 0.2);
}

.cta-glow-2 {
  bottom: -200px;
  right: -100px;
  background: rgba(239, 68, 68, 0.15);
}

.cta-content {
  position: relative;
  z-index: 1;
  padding: 3rem;
}

/* Header */
.cta-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.cta-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(239, 68, 68, 0.1));
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 100px;
  margin-bottom: 1.5rem;
}

.cta-badge-dot {
  width: 6px;
  height: 6px;
  background: #f59e0b;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.cta-badge-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: #f59e0b;
}

.cta-title {
  font-family: var(--lp-font-display);
  font-size: clamp(1.75rem, 4vw, 2.25rem);
  font-weight: 800;
  margin-bottom: 0.75rem;
  color: var(--lp-text-primary);
}

.cta-subtitle {
  font-size: 1.1rem;
  color: var(--lp-text-tertiary);
}

.cta-subtitle strong {
  color: #f59e0b;
  font-weight: 700;
}

/* Main content - form and qrcode */
.cta-main {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 2rem;
  align-items: flex-start;
}

/* Contact form */
.contact-form-wrapper {
  padding: 1.5rem;
  background: var(--lp-bg-secondary);
  border: 1px solid var(--lp-border-subtle);
  border-radius: 16px;
}

.form-title {
  font-family: var(--lp-font-display);
  font-size: 1rem;
  font-weight: 600;
  color: var(--lp-text-primary);
  margin-bottom: 1.25rem;
}

.contact-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--lp-text-secondary);
}

.form-group input {
  padding: 0.75rem 1rem;
  background: var(--lp-bg-card);
  border: 1px solid var(--lp-border-default);
  border-radius: 8px;
  font-size: 0.95rem;
  color: var(--lp-text-primary);
  transition: all 0.2s ease;
}

.form-group input::placeholder {
  color: var(--lp-text-muted);
}

.form-group input:focus {
  outline: none;
  border-color: var(--lp-primary-500);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.submit-btn {
  margin-top: 0.5rem;
  padding: 0.875rem 1.5rem;
  background: var(--lp-gradient-primary);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Success message */
.success-message {
  text-align: center;
  padding: 2rem 1rem;
}

.success-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(16, 185, 129, 0.15);
  border-radius: 50%;
  color: #10b981;
  font-size: 1.5rem;
  font-weight: bold;
}

.success-message h4 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--lp-text-primary);
  margin-bottom: 0.5rem;
}

.success-message p {
  color: var(--lp-text-secondary);
}

/* Divider */
.divider {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 1rem;
}

.divider span {
  padding: 0.5rem 0.75rem;
  background: var(--lp-bg-tertiary);
  border: 1px solid var(--lp-border-subtle);
  border-radius: 8px;
  font-size: 0.85rem;
  color: var(--lp-text-muted);
}

/* WeChat QRCode */
.wechat-wrapper {
  text-align: center;
  padding: 1.5rem;
  background: var(--lp-bg-secondary);
  border: 1px solid var(--lp-border-subtle);
  border-radius: 16px;
}

.wechat-title {
  font-family: var(--lp-font-display);
  font-size: 1rem;
  font-weight: 600;
  color: var(--lp-text-primary);
  margin-bottom: 1.25rem;
}

.qrcode-placeholder {
  margin-bottom: 1rem;
}

.qrcode-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--lp-bg-card);
  border: 2px dashed var(--lp-border-default);
  border-radius: 12px;
  color: var(--lp-text-muted);
}

.qrcode-hint {
  font-size: 0.75rem;
  color: var(--lp-text-muted);
}

.wechat-desc {
  font-size: 0.85rem;
  color: var(--lp-text-tertiary);
}

/* Features */
.cta-features {
  display: flex;
  gap: 2rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 2.5rem;
  padding-top: 2rem;
  border-top: 1px solid var(--lp-border-subtle);
}

.cta-feature {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: var(--lp-text-tertiary);
}

.cta-feature svg {
  color: #10b981;
}

/* Responsive */
@media (max-width: 768px) {
  .cta-main {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .divider {
    padding: 1rem 0;
  }

  .divider span {
    width: 100%;
    text-align: center;
  }

  .cta-content {
    padding: 2rem 1.5rem;
  }
}
</style>
