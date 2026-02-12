"""导入服务

负责从 Excel 文件批量导入反馈
"""

from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.feedalyze.crud import crud_customer, crud_feedback
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

    async def import_excel(
        self,
        db: AsyncSession,
        tenant_id: str,
        file: UploadFile,
        generate_summary: bool = True,
    ) -> dict[str, Any]:
        """
        导入 Excel 文件

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            file: 上传的文件
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
                    'allowed': settings.IMPORT_ALLOWED_EXTENSIONS
                }

            # 2. 读取文件
            try:
                content = await file.read()
                
                if len(content) > settings.IMPORT_MAX_FILE_SIZE:
                    return {
                        'status': 'error',
                        'message': f'文件过大: {len(content)} bytes, 最大允许: {settings.IMPORT_MAX_FILE_SIZE}'
                    }

                # 根据文件类型读取
                if file_ext in ['xlsx', 'xls']:
                    df = pd.read_excel(content)
                elif file_ext == 'csv':
                    df = pd.read_csv(content)
                else:
                    return {'status': 'error', 'message': f'不支持的文件格式: {file_ext}'}

            except Exception as e:
                log.error(f'Failed to read file: {e}')
                return {'status': 'error', 'message': f'文件读取失败: {str(e)}'}

            # 3. 验证必填列
            required_columns = ['反馈内容', '客户名称']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return {
                    'status': 'error',
                    'message': f'缺少必填列: {", ".join(missing_columns)}',
                    'required_columns': required_columns,
                    'found_columns': list(df.columns)
                }

            log.info(f'Excel loaded: {len(df)} rows, columns: {list(df.columns)}')

            # 4. 逐行导入
            success_count = 0
            errors = []

            for idx, row in df.iterrows():
                try:
                    # 跳过空行
                    if pd.isna(row['反馈内容']) or not str(row['反馈内容']).strip():
                        continue

                    # 获取或创建客户
                    customer_name = str(row['客户名称']).strip()
                    customer_type_raw = row.get('客户类型', 'normal')
                    customer_type = self.CUSTOMER_TYPE_MAP.get(str(customer_type_raw).strip(), 'normal')

                    customer = await self._get_or_create_customer(
                        db=db,
                        tenant_id=tenant_id,
                        name=customer_name,
                        customer_type=customer_type
                    )

                    # 解析提交时间
                    submitted_at = timezone.now()
                    if '提交时间' in row and not pd.isna(row['提交时间']):
                        try:
                            submitted_at = pd.to_datetime(row['提交时间'])
                        except:
                            pass

                    # 判断是否紧急
                    is_urgent = False
                    if '是否紧急' in row and not pd.isna(row['是否紧急']):
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
                        customer_id=customer.id,
                        content=content,
                        source='import',
                        is_urgent=is_urgent,
                        ai_summary=ai_summary,
                        submitted_at=submitted_at
                    )

                    success_count += 1

                except Exception as e:
                    error_msg = f'第 {idx + 2} 行导入失败: {str(e)}'
                    log.warning(error_msg)
                    errors.append({
                        'row': idx + 2,  # Excel 行号（从1开始，表头占1行）
                        'error': str(e),
                        'content': str(row.get('反馈内容', ''))[:50]
                    })

            log.info(f'Import completed: {success_count} success, {len(errors)} errors')

            return {
                'status': 'completed',
                'total': len(df),
                'success': success_count,
                'failed': len(errors),
                'errors': errors[:20],  # 最多返回 20 条错误
                'has_more_errors': len(errors) > 20
            }

        except Exception as e:
            log.error(f'Import failed: {e}')
            return {
                'status': 'error',
                'message': str(e),
                'total': 0,
                'success': 0,
                'failed': 0
            }

    async def _get_or_create_customer(
        self,
        db: AsyncSession,
        tenant_id: str,
        name: str,
        customer_type: str
    ):
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
            business_value=business_value
        )

    def generate_template(self) -> pd.DataFrame:
        """
        生成 Excel 导入模板

        Returns:
            模板 DataFrame
        """
        template_data = {
            '反馈内容': ['示例：登录速度太慢，希望能优化', '示例：导出功能经常失败'],
            '客户名称': ['小米科技', '字节跳动'],
            '客户类型': ['strategic', 'major'],
            '提交时间': ['2025-01-01', '2025-01-02'],
            '是否紧急': ['否', '是']
        }

        return pd.DataFrame(template_data)


import_service = ImportService()
