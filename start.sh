#!/bin/bash

# 启动脚本 - 在后台运行前后端服务

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 创建日志目录
mkdir -p logs

echo "🚀 正在启动服务..."

# 检查端口是否已被占用
if lsof -Pi :6000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口 6000 已被占用，正在停止现有服务..."
    ./stop.sh
    sleep 2
fi

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口 5173 已被占用，正在停止现有服务..."
    ./stop.sh
    sleep 2
fi

# 启动后端服务
echo "📦 启动后端服务 (端口 6000)..."
cd backend
nohup uv run python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
cd ..

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 3

# 检查后端是否启动成功
if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "❌ 后端服务启动失败，请查看日志: logs/backend.log"
    exit 1
fi

# 启动前端服务
echo "🎨 启动前端服务 (端口 5173)..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..

# 等待前端启动
echo "⏳ 等待前端服务启动..."
sleep 5

# 检查前端是否启动成功
if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "❌ 前端服务启动失败，请查看日志: logs/frontend.log"
    exit 1
fi

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "📊 服务状态："
echo "  - 后端服务: http://localhost:6000 (PID: $BACKEND_PID)"
echo "  - 前端服务: http://localhost:5173 (PID: $FRONTEND_PID)"
echo ""
echo "📝 日志文件："
echo "  - 后端日志: logs/backend.log"
echo "  - 前端日志: logs/frontend.log"
echo ""
echo "🛑 停止服务：运行 ./stop.sh"
echo ""
echo "💡 查看实时日志："
echo "  tail -f logs/backend.log    # 后端日志"
echo "  tail -f logs/frontend.log   # 前端日志"

