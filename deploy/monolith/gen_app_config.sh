#!/bin/bash
# 动态生成前端配置文件 _app.config.js
# 从容器环境变量读取配置，运行时注入到前端

set -e

CONFIG_FILE="/var/www/fba_ui/_app.config.js"
WINDOW_VAR="_VBEN_ADMIN_PRO_APP_CONF_"

# 默认值
APP_TITLE="${VITE_APP_TITLE:-回响}"
API_URL="${VITE_GLOB_API_URL:-/}"
APP_NAMESPACE="${VITE_APP_NAMESPACE:-userecho-admin}"
DEVTOOLS="${VITE_DEVTOOLS:-false}"
DEMO_MODE="${VITE_DEMO_MODE:-false}"
TURNSTILE_SITE_KEY="${VITE_TURNSTILE_SITE_KEY:-}"

# 生成 JSON 配置
cat > "$CONFIG_FILE" << EOF
window.${WINDOW_VAR}={
  "VITE_APP_TITLE": "${APP_TITLE}",
  "VITE_GLOB_API_URL": "${API_URL}",
  "VITE_APP_NAMESPACE": "${APP_NAMESPACE}",
  "VITE_DEVTOOLS": ${DEVTOOLS},
  "VITE_DEMO_MODE": ${DEMO_MODE},
  "VITE_TURNSTILE_SITE_KEY": "${TURNSTILE_SITE_KEY}"
};
Object.freeze(window.${WINDOW_VAR});
Object.defineProperty(window,"${WINDOW_VAR}",{configurable:false,writable:false});
EOF

echo "[gen_app_config.sh] Generated ${CONFIG_FILE}"
echo "[gen_app_config.sh] API_URL=${API_URL}, DEMO_MODE=${DEMO_MODE}"
