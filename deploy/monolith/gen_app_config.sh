#!/bin/bash
# 动态生成前端配置文件 _app.config.js
# 从容器环境变量读取配置，运行时注入到前端

set -e

CONFIG_FILE="/var/www/fba_ui/_app.config.js"
WINDOW_VAR="_VBEN_ADMIN_PRO_APP_CONF_"

# 布尔值严格规范化：只输出 "true" 或 "false"，消除所有边界情况
# 兼容 true/TRUE/True/1/yes/on 及其反面，同时清理空格和 \r 字符
normalize_bool() {
  local val
  val=$(printf '%s' "${1:-false}" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
  case "$val" in
    true|1|yes|on) echo "true" ;;
    *) echo "false" ;;
  esac
}

# 读取环境变量（支持 VITE_APP_TITLE 和 APP_TITLE 两种命名风格）
APP_TITLE="${VITE_APP_TITLE:-${APP_TITLE:-回响}}"
API_URL="${VITE_GLOB_API_URL:-/}"
APP_NAMESPACE="${VITE_APP_NAMESPACE:-userecho-admin}"
TURNSTILE_SITE_KEY="${VITE_TURNSTILE_SITE_KEY:-}"

# 布尔值必须经过 normalize_bool，杜绝 TRUE/FALSE/True 等无效 JS 值
DEVTOOLS=$(normalize_bool "${VITE_DEVTOOLS:-false}")
DEMO_MODE=$(normalize_bool "${VITE_DEMO_MODE:-${DEMO_MODE:-false}}")

# 生成 JS 配置（所有值必须是双引号包裹的字符串）
cat > "$CONFIG_FILE" << EOF
window.${WINDOW_VAR}={
  "VITE_APP_TITLE": "${APP_TITLE}",
  "VITE_GLOB_API_URL": "${API_URL}",
  "VITE_APP_NAMESPACE": "${APP_NAMESPACE}",
  "VITE_DEVTOOLS": "${DEVTOOLS}",
  "VITE_DEMO_MODE": "${DEMO_MODE}",
  "VITE_TURNSTILE_SITE_KEY": "${TURNSTILE_SITE_KEY}"
};
Object.freeze(window.${WINDOW_VAR});
Object.defineProperty(window,"${WINDOW_VAR}",{configurable:false,writable:false});
EOF

echo "[gen_app_config.sh] Generated ${CONFIG_FILE}"
echo "[gen_app_config.sh] APP_TITLE=${APP_TITLE}, API_URL=${API_URL}, DEMO_MODE=${DEMO_MODE}, DEVTOOLS=${DEVTOOLS}"
