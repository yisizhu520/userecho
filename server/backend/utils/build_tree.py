import operator

from collections.abc import Sequence
from typing import Any

from backend.common.enums import BuildTreeType
from backend.utils.serializers import RowData, select_list_serialize


def _normalize_vben_component(component: str | None) -> str | None:
    """
    Normalize component string for vben admin route resolving.

    目标：把各种“人写出来的脏格式”统一成类似 `/dashboard/analytics/index` 这种
    可被前端 `import.meta.glob()` 映射到的 key。
    """
    if not component:
        return None

    c = component.strip().replace('\\', '/')
    if not c:
        return None

    # 常见错误：把路由前缀也塞进了 component（它应该是 views 路径，不是 route path）
    for prefix in ('/app/', '/admin/'):
        if c.startswith(prefix):
            c = c[len(prefix) - 1 :]  # keep leading '/'
            break

    # 常见错误：带了 .vue 后缀
    c = c.removesuffix('.vue')

    # 常见错误：带了 views 目录前缀或别名
    for prefix in ('#/views/', '/views/', 'views/', 'src/views/', '/src/views/'):
        if c.startswith(prefix):
            c = '/' + c[len(prefix) :]
            break

    if not c.startswith('/'):
        c = '/' + c

    # 去掉多余的斜杠（保留开头那个）
    while '//' in c:
        c = c.replace('//', '/')

    return c


def get_tree_nodes(row: Sequence[RowData], *, is_sort: bool, sort_key: str) -> list[dict[str, Any]]:
    """
    获取所有树形结构节点

    :param row: 原始数据行序列
    :param is_sort: 是否启用结果排序
    :param sort_key: 基于此键对结果进行进行排序
    :return:
    """
    tree_nodes = select_list_serialize(row)
    if is_sort:
        tree_nodes.sort(key=operator.itemgetter(sort_key))
    return tree_nodes


def traversal_to_tree(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    通过遍历算法构造树形结构

    :param nodes: 树节点列表
    :return:
    """
    tree: list[dict[str, Any]] = []
    node_dict = {node['id']: node for node in nodes}

    for node in nodes:
        parent_id = node['parent_id']
        if parent_id is None:
            tree.append(node)
        else:
            parent_node = node_dict.get(parent_id)
            if parent_node is not None:
                if 'children' not in parent_node:
                    parent_node['children'] = []
                if node not in parent_node['children']:
                    parent_node['children'].append(node)
            else:
                if node not in tree:
                    tree.append(node)

    return tree


def recursive_to_tree(nodes: list[dict[str, Any]], *, parent_id: int | None = None) -> list[dict[str, Any]]:
    """
    通过递归算法构造树形结构（性能影响较大）

    :param nodes: 树节点列表
    :param parent_id: 父节点 ID，默认为 None 表示根节点
    :return:
    """
    tree: list[dict[str, Any]] = []
    for node in nodes:
        if node['parent_id'] == parent_id:
            child_nodes = recursive_to_tree(nodes, parent_id=node['id'])
            if child_nodes:
                node['children'] = child_nodes
            tree.append(node)
    return tree


def get_tree_data(
    row: Sequence[RowData],
    build_type: BuildTreeType = BuildTreeType.traversal,
    *,
    parent_id: int | None = None,
    is_sort: bool = True,
    sort_key: str = 'sort',
) -> list[dict[str, Any]]:
    """
    获取树形结构数据

    :param row: 原始数据行序列
    :param build_type: 构建树形结构的算法类型，默认为遍历算法
    :param parent_id: 父节点 ID，仅在递归算法中使用
    :param is_sort: 是否启用结果排序
    :param sort_key: 基于此键对结果进行进行排序
    :return:
    """
    nodes = get_tree_nodes(row, is_sort=is_sort, sort_key=sort_key)
    match build_type:
        case BuildTreeType.traversal:
            tree = traversal_to_tree(nodes)
        case BuildTreeType.recursive:
            tree = recursive_to_tree(nodes, parent_id=parent_id)
        case _:
            raise ValueError(f'无效的算法类型：{build_type}')
    return tree


def get_vben5_tree_data(
    row: Sequence[RowData],
    *,
    is_sort: bool = True,
    sort_key: str = 'sort',
) -> list[dict[str, Any]]:
    """
    获取 vben5 菜单树形结构数据

    :param row: 原始数据行序列
    :param is_sort: 是否启用结果排序
    :param sort_key: 基于此键对结果进行进行排序
    :return:
    """
    meta_keys = {'title', 'icon', 'link', 'cache', 'display', 'status'}

    vben5_nodes = [
        {
            **{k: v for k, v in node.items() if k not in meta_keys},
            # 关键：保证 component 可被前端正确解析，否则会出现"点击菜单内容区空白但无报错"
            'component': _normalize_vben_component(node.get('component')),
            'meta': {
                'title': node['title'],
                'icon': node['icon'],
                'iframeSrc': node['link'] if node['type'] == 3 else '',
                'link': node['link'] if node['type'] == 4 else '',
                'keepAlive': bool(node['cache']),
                'hideInMenu': not bool(node['display']),
                'menuVisibleWithForbidden': not bool(node['status']),
            },
        }
        for node in get_tree_nodes(row, is_sort=is_sort, sort_key=sort_key)
    ]

    # 兜底：iframe/外链如果没配 component，给一个明确的页面容器，避免 router-view 直接空
    for n in vben5_nodes:
        if n.get('type') in (3, 4) and not n.get('component'):
            n['component'] = '/_core/fallback/iframe'

    tree = traversal_to_tree(vben5_nodes)

    def _first_visible_child_path(node: dict[str, Any]) -> str | None:
        """获取第一个可见子节点的路径，用于设置目录的 redirect"""
        children = node.get('children') or []
        for ch in children:
            if not isinstance(ch, dict):
                continue
            meta = ch.get('meta') or {}
            if not isinstance(meta, dict):
                continue
            # 跳过隐藏菜单
            if meta.get('hideInMenu'):
                continue
            path = ch.get('path')
            if path and isinstance(path, str):
                return path
        return None

    def _fill_redirect(nodes: list[dict[str, Any]]) -> None:
        """为目录节点填充 redirect，避免点击目录时内容区空白"""
        for n in nodes:
            if not isinstance(n, dict):
                continue

            children = n.get('children') or []
            # 先递归处理子节点
            if children and isinstance(children, list):
                _fill_redirect(children)

            # 目录(type=0)没有 component 时，必须设置 redirect，否则内容区会空白
            if n.get('type') == 0 and not n.get('component'):
                if not n.get('redirect'):  # 只在没有手动设置时才自动填充
                    redirect = _first_visible_child_path(n)
                    if redirect:
                        n['redirect'] = redirect
                        # Debug 日志：确保 redirect 被正确设置
                        # print(f"[DEBUG] Set redirect for '{n.get('name')}': {redirect}")

    _fill_redirect(tree)
    return tree
