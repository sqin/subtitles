#!/bin/bash

# 停止脚本 - 停止前后端服务

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🛑 正在停止服务..."

# 停止后端服务
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "📦 停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 1
        # 如果还在运行，强制杀死
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill -9 $BACKEND_PID
        fi
        echo "✅ 后端服务已停止"
    else
        echo "⚠️  后端服务未运行 (PID: $BACKEND_PID)"
    fi
    rm -f logs/backend.pid
else
    echo "⚠️  未找到后端 PID 文件"
    # 尝试通过端口查找并杀死
    BACKEND_PID=$(lsof -ti:6000 2>/dev/null)
    if [ ! -z "$BACKEND_PID" ]; then
        echo "📦 通过端口查找并停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo "✅ 后端服务已停止"
    fi
fi

# 停止前端服务
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🎨 停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 1
        # 如果还在运行，强制杀死
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill -9 $FRONTEND_PID
        fi
        echo "✅ 前端服务已停止"
    else
        echo "⚠️  前端服务未运行 (PID: $FRONTEND_PID)"
    fi
    rm -f logs/frontend.pid
else
    echo "⚠️  未找到前端 PID 文件"
    # 尝试通过端口查找并杀死
    FRONTEND_PID=$(lsof -ti:5173 2>/dev/null)
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "🎨 通过端口查找并停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo "✅ 前端服务已停止"
    fi
fi

echo ""
echo "✅ 所有服务已停止"

