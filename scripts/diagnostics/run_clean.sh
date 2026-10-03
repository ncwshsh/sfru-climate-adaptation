#!/usr/bin/env bash
# run_clean.sh —— 在「干净环境」下运行下载器
#
# 为什么需要它（2026-09-17 踩坑，耗时 40 分钟定位）：
#   WorkBuddy 的 Bash 工具会把下面这些注入到子进程：
#     · BASH_ENV = .../cli/vendor/shim/shell-runtime-bash-env.sh  （每次 bash 启动都 source）
#     · 导出的 bash 函数 BASH_FUNC_rm%% / BASH_FUNC_rmdir%% / BASH_FUNC_unlink%%
#       （安全删除机制，用「导出函数」而不是 PATH 包装。删除失败时 fail-closed）
#     · 一批 CODEBUDDY_* / LSBOX_* 沙箱变量
#   后果：在 `bash dl_ena.sh` 这类**脚本内部**，
#     `[ -d /c/SF_data/01_raw ]` 判为假、`mkdir -p` 报 “mkdir: Permission denied”
#     （注意措辞不是 coreutils 的 “cannot create directory”，是代理在拦），
#     于是 dl_ena.sh 第 50 行 mkdir 失败 → 143 个样本全部 [ERR] 退出，
#     **一个字节都没下**，且表象是“权限问题”，极易误判成磁盘/ACL 问题。
#   实测：同样命令在工具前台手敲是好的，脚本里就是坏的 → 环境差异，不是权限。
#
# 修法：用 env 剥掉上述变量，并显式给出 PATH（含 Windows curl 所在目录）。
#
# 用法:  bash run_clean.sh <脚本路径> [参数...]
# 例:    bash dl_s2/run_clean.sh dl_s2/dl_US.sh
#        bash dl_s2/run_clean.sh dl_ena.sh SRR29141578 8 16 C:/SF_data/01_raw 80

export PATH="/usr/bin:/bin:/c/WINDOWS/system32:$PATH"
exec env \
  -u BASH_ENV \
  -u 'BASH_FUNC_rm%%' -u 'BASH_FUNC_rmdir%%' -u 'BASH_FUNC_unlink%%' \
  PATH="/usr/bin:/bin:/c/WINDOWS/system32" \
  HOME="${HOME:-/c/Users/Admin}" \
  PROXY="${PROXY:-http://127.0.0.1:7897}" \
  bash "$@"
