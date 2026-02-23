import type { VxeGridProps } from '#/adapter/vxe-table';

export const columns: VxeGridProps['columns'] = [
    {
        field: 'tenant_id',
        title: 'Tenant ID',
        width: 200,
    },
    {
        field: 'plan.name',
        title: '套餐名称',
    },
    {
        field: 'plan.code',
        title: '套餐代码',
    },
    {
        field: 'status',
        title: '状态',
        slots: { default: 'status' },
    },
    {
        field: 'started_at',
        title: '开始时间',
    },
    {
        field: 'expires_at',
        title: '过期时间',
    },
    {
        title: '操作',
        field: 'action',
        fixed: 'right',
        width: 120,
        slots: { default: 'action' },
    },
];
