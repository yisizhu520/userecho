"""导入服务

负责从 Excel 文件批量导入反馈
"""

from io import BytesIO, StringIO
from typing import Any

import pandas as pd

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.userecho.crud import crud_board, crud_customer, crud_feedback
from backend.common.log import log
from backend.core.conf import settings
from backend.utils.ai_client import ai_client
from backend.utils.timezone import timezone


class ImportService:
    """Excel 导入服务"""

    # 客户类型映射
    CUSTOMER_TYPE_MAP = {
        '普通': 'normal',
        '付费': 'paid',
        '大客户': 'major',
        '战略客户': 'strategic',
        'normal': 'normal',
        'paid': 'paid',
        'major': 'major',
        'strategic': 'strategic',
    }

    # 商业价值映射
    BUSINESS_VALUE_MAP = {
        'normal': 1,
        'paid': 3,
        'major': 5,
        'strategic': 10,
    }

    # 必填列和可选列定义
    REQUIRED_COLUMNS = ['反馈内容']
    OPTIONAL_COLUMNS = ['看板名称', '客户名称', '客户类型', '提交时间', '是否紧急']

    def _read_file_content(self, content: bytes, file_ext: str) -> pd.DataFrame | dict:
        """
        读取文件内容并返回 DataFrame

        Args:
            content: 文件字节内容
            file_ext: 文件扩展名

        Returns:
            DataFrame 或错误字典
        """
        try:
            if file_ext in ['xlsx', 'xls']:
                excel_io = BytesIO(content)
                if file_ext == 'xlsx':
                    return pd.read_excel(excel_io, engine='openpyxl')
                return pd.read_excel(excel_io)
            if file_ext == 'csv':
                text = content.decode('utf-8-sig', errors='replace')
                return pd.read_csv(StringIO(text))
            return {'status': 'error', 'message': f'不支持的文件格式: {file_ext}'}
        except ImportError as e:
            missing = str(e)
            if 'openpyxl' in missing:
                return {'status': 'error', 'message': '服务端缺少依赖 openpyxl'}
            if 'xlrd' in missing:
                return {'status': 'error', 'message': '服务端缺少依赖 xlrd'}
            raise

    async def preview_excel(self, file: UploadFile) -> dict:
        """
        预览 Excel 文件，返回列检测和样本数据

        Args:
            file: 上传的文件

        Returns:
            预览结果字典
        """
        try:
            # 1. 验证文件
            if not file.filename:
                return {'status': 'error', 'message': '文件名为空'}

            file_ext = file.filename.lower().split('.')[-1]
            if f'.{file_ext}' not in settings.IMPORT_ALLOWED_EXTENSIONS:
                return {'status': 'error', 'message': f'不支持的文件格式: {file_ext}'}

            # 2. 读取文件
            content = await file.read()
            if len(content) > settings.IMPORT_MAX_FILE_SIZE:
                return {'status': 'error', 'message': f'文件过大: {len(content)} bytes'}

            result = self._read_file_content(content, file_ext)
            if isinstance(result, dict):
                return result
            df = result

            # 3. 检测列
            detected = list(df.columns)
            missing_required = [c for c in self.REQUIRED_COLUMNS if c not in detected]
            missing_optional = [c for c in self.OPTIONAL_COLUMNS if c not in detected]

            # 4. 构建预览数据
            sample = df.head(5).fillna('').astype(str).to_dict('records')

            return {
                'status': 'error' if missing_required else 'ready',
                'message': f'缺少必填列: {", ".join(missing_required)}' if missing_required else None,
                'total_rows': len(df),
                'sample_data': sample,
                'detected_columns': detected,
                'missing_required': missing_required,
                'missing_optional': missing_optional,
            }
        except Exception as e:
            log.error(f'Preview failed: {e}')
            return {'status': 'error', 'message': f'文件解析失败: {e!s}'}

    async def import_excel(
        self,
        db: AsyncSession,
        tenant_id: str,
        file: UploadFile,
        default_board_id: str | None = None,
        default_customer_name: str | None = None,
        use_anonymous: bool = False,
        generate_summary: bool = True,
    ) -> dict[str, Any]:
        """
        导入 Excel 文件

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            file: 上传的文件
            default_board_id: 默认看板ID（当 Excel 无看板列时使用）
            default_customer_name: 默认客户名称（当 Excel 无客户列时使用）
            use_anonymous: 是否使用匿名（优先级高于 default_customer_name）
            generate_summary: 是否生成 AI 摘要

        Returns:
            导入结果统计
        """
        try:
            log.info(f'Starting Excel import for tenant: {tenant_id}')

            # 1. 验证文件
            if not file.filename:
                return {'status': 'error', 'message': '文件名为空'}

            file_ext = file.filename.lower().split('.')[-1]
            if f'.{file_ext}' not in settings.IMPORT_ALLOWED_EXTENSIONS:
                return {
                    'status': 'error',
                    'message': f'不支持的文件格式: {file_ext}',
                    'allowed': settings.IMPORT_ALLOWED_EXTENSIONS,
                }

            # 2. 读取文件
            try:
                content = await file.read()

                if len(content) > settings.IMPORT_MAX_FILE_SIZE:
                    return {
                        'status': 'error',
                        'message': f'文件过大: {len(content)} bytes, 最大允许: {settings.IMPORT_MAX_FILE_SIZE}',
                    }

                # 根据文件类型读取
                if file_ext in ['xlsx', 'xls']:
                    excel_io = BytesIO(content)
                    try:
                        if file_ext == 'xlsx':
                            df = pd.read_excel(excel_io, engine='openpyxl')
                        else:
                            df = pd.read_excel(excel_io)
                    except ImportError as e:
                        missing = str(e)
                        if 'openpyxl' in missing:
                            return {
                                'status': 'error',
                                'message': '服务端缺少依赖 openpyxl，无法解析 .xlsx 文件，请安装 openpyxl 后重试',
                            }
                        if 'xlrd' in missing:
                            return {
                                'status': 'error',
                                'message': '服务端缺少依赖 xlrd，无法解析 .xls 文件，请安装 xlrd 后重试',
                            }
                        raise
                elif file_ext == 'csv':
                    text = content.decode('utf-8-sig', errors='replace')
                    df = pd.read_csv(StringIO(text))
                else:
                    return {'status': 'error', 'message': f'不支持的文件格式: {file_ext}'}

            except Exception as e:
                log.error(f'Failed to read file for tenant {tenant_id}, filename={file.filename}: {e}')
                return {'status': 'error', 'message': f'文件读取失败: {e!s}'}

            # 3. 验证必填列（仅反馈内容）
            if '反馈内容' not in df.columns:
                return {
                    'status': 'error',
                    'message': '缺少必填列: 反馈内容',
                    'required_columns': ['反馈内容'],
                    'found_columns': list(df.columns),
                }

            # 检查看板配置
            has_board_column = '看板名称' in df.columns
            if not has_board_column and not default_board_id:
                return {
                    'status': 'error',
                    'message': '缺少「看板名称」列，请在配置中选择目标看板',
                }

            # 验证 default_board_id 合法性
            default_board = None
            if default_board_id:
                default_board = await crud_board.get_by_id(db, tenant_id, default_board_id)
                if not default_board:
                    return {'status': 'error', 'message': f'指定的默认看板不存在: {default_board_id}'}

            log.debug(f'Excel loaded: {len(df)} rows, columns: {list(df.columns)}')

            # 4. 逐行导入
            success_count = 0
            errors = []

            for idx, row in df.iterrows():
                try:
                    # 跳过空行
                    if pd.isna(row['反馈内容']) or not str(row['反馈内容']).strip():
                        continue

                    # 获取看板（优先 Excel 列，其次 default_board_id）
                    board = None
                    if has_board_column and pd.notna(row.get('看板名称')) and str(row['看板名称']).strip():
                        board_name = str(row['看板名称']).strip()
                        board = await crud_board.get_by_name(db, tenant_id, board_name)
                        if not board:
                            errors.append({
                                'row': idx + 2,
                                'error': f'看板不存在: {board_name}',
                                'content': str(row['反馈内容'])[:50],
                            })
                            continue
                    else:
                        board = default_board

                    if not board:
                        errors.append({'row': idx + 2, 'error': '看板未指定', 'content': str(row['反馈内容'])[:50]})
                        continue

                    # 处理客户（优先 Excel 列，其次 default_customer_name，最后匿名）
                    has_customer_column = '客户名称' in df.columns
                    customer_id = None
                    anonymous_author = None

                    if has_customer_column and pd.notna(row.get('客户名称')) and str(row['客户名称']).strip():
                        customer_name = str(row['客户名称']).strip()
                        customer_type_raw = row.get('客户类型', 'normal')
                        customer_type = self.CUSTOMER_TYPE_MAP.get(
                            str(customer_type_raw).strip() if pd.notna(customer_type_raw) else 'normal', 'normal'
                        )
                        customer = await self._get_or_create_customer(
                            db=db, tenant_id=tenant_id, name=customer_name, customer_type=customer_type
                        )
                        customer_id = customer.id
                    elif not use_anonymous and default_customer_name:
                        customer = await self._get_or_create_customer(
                            db=db, tenant_id=tenant_id, name=default_customer_name, customer_type='normal'
                        )
                        customer_id = customer.id
                    else:
                        anonymous_author = '匿名导入用户'

                    # 解析提交时间
                    submitted_at = timezone.now()
                    if '提交时间' in row and pd.notna(row['提交时间']):
                        try:
                            # pd.to_datetime 返回 tz-naive Timestamp，需要转为 timezone-aware
                            dt = pd.to_datetime(row['提交时间'])
                            # 转为 Python datetime
                            if hasattr(dt, 'to_pydatetime'):
                                dt = dt.to_pydatetime()
                            # 添加时区信息（假定输入为本地时区时间）
                            submitted_at = dt.replace(tzinfo=timezone.tz_info) if dt.tzinfo is None else dt
                        except:
                            pass

                    # 判断是否紧急
                    is_urgent = False
                    if '是否紧急' in row and pd.notna(row['是否紧急']):
                        is_urgent_raw = str(row['是否紧急']).strip().lower()
                        is_urgent = is_urgent_raw in ['是', 'true', '1', 'yes', '紧急']

                    # 反馈内容
                    content = str(row['反馈内容']).strip()

                    # 生成 AI 摘要（可选）
                    ai_summary = None
                    if generate_summary:
                        ai_summary = await ai_client.generate_summary(content, max_length=20)

                    # 创建反馈
                    from backend.database.db import uuid4_str

                    await crud_feedback.create(
                        db=db,
                        tenant_id=tenant_id,
                        id=uuid4_str(),
                        board_id=board.id,
                        customer_id=customer_id,
                        anonymous_author=anonymous_author,
                        content=content,
                        source='import',
                        is_urgent=is_urgent,
                        ai_summary=ai_summary,
                        submitted_at=submitted_at,
                    )

                    success_count += 1

                except Exception as e:
                    error_msg = f'第 {idx + 2} 行导入失败: {e!s}'
                    log.warning(error_msg)
                    errors.append({
                        'row': idx + 2,  # Excel 行号（从1开始，表头占1行）
                        'error': str(e),
                        'content': str(row.get('反馈内容', ''))[:50],
                    })

            log.info(
                f'Excel import completed for tenant {tenant_id}: {success_count} success, {len(errors)} errors, file: {file.filename}'
            )

            return {
                'status': 'completed',
                'total': len(df),
                'success': success_count,
                'failed': len(errors),
                'errors': errors[:20],  # 最多返回 20 条错误
                'has_more_errors': len(errors) > 20,
            }

        except Exception as e:
            log.error(f'Excel import failed for tenant {tenant_id}, file {file.filename}: {e}')
            return {'status': 'error', 'message': str(e), 'total': 0, 'success': 0, 'failed': 0}

    async def _get_or_create_customer(self, db: AsyncSession, tenant_id: str, name: str, customer_type: str):
        """
        获取或创建客户

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            name: 客户名称
            customer_type: 客户类型

        Returns:
            客户实例
        """
        # 先查询
        customer = await crud_customer.get_by_name(db, tenant_id, name)
        if customer:
            return customer

        # 创建新客户
        business_value = self.BUSINESS_VALUE_MAP.get(customer_type, 1)

        from backend.database.db import uuid4_str

        return await crud_customer.create(
            db=db,
            tenant_id=tenant_id,
            id=uuid4_str(),
            name=name,
            customer_type=customer_type,
            business_value=business_value,
        )

    def generate_template(self) -> pd.DataFrame:
        """
        生成 Excel 导入模板

        Returns:
            模板 DataFrame
        """
        template_data = {
            '看板名称': ['移动端反馈', 'Web端反馈'],
            '反馈内容': ['示例：登录速度太慢，希望能优化', '示例：导出功能经常失败'],
            '客户名称': ['小米科技', ''],
            '客户类型': ['strategic', ''],
            '提交时间': ['2025-01-01', '2025-01-02'],
            '是否紧急': ['否', '是'],
        }

        return pd.DataFrame(template_data)


import_service = ImportService()
