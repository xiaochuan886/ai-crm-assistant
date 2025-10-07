---
name: frontend-widget-architecture
status: backlog
created: 2025-10-07T05:17:58Z
progress: 0%
prd: .claude/prds/frontend-architecture-overhaul.md
github: https://github.com/xiaochuan886/ai-crm-assistant/issues/1
---

# Epic: frontend-widget-architecture

## Overview
重构 AI CRM Assistant 前端为嵌入式 Widget 架构，采用 Vercel AI SDK + shadcn/ui 技术栈，专门针对 iframe 场景优化。核心目标是创建一个安全、高性能、易于集成的嵌入式 AI Widget，可无缝嵌入到现有 CRM 系统中。

## Architecture Decisions

### 核心架构选择
- **嵌入式优先**: 以 iframe 嵌入为核心部署方式，确保跨域安全性
- **组件化设计**: 采用 React + TypeScript 实现高度可复用的组件系统
- **现代化技术栈**: Vercel AI SDK 负责 AI 交互，shadcn/ui 提供基础组件
- **性能优化**: 代码分割、懒加载、虚拟滚动确保 Widget 轻量级

### 跨域通信策略
- **postMessage API**: 实现安全的父子页面通信
- **消息验证**: 采用 JWT 签名验证消息来源和完整性
- **事件驱动**: 设计标准化的事件协议支持双向通信
- **沙箱隔离**: 严格的 CSP 策略和 iframe sandbox 属性

### 状态管理架构
- **Zustand**: 轻量级客户端状态管理
- **React Query**: 服务端状态缓存和同步
- **Context API**: 组件间共享状态
- **跨 iframe 同步**: 通过 postMessage 实现状态同步

## Technical Approach

### Widget 核心组件
- **WidgetContainer**: 主容器组件，负责生命周期管理
- **WidgetBridge**: 跨域通信桥接组件
- **ChatInterface**: AI 聊天界面，集成 Vercel AI SDK
- **ThemeProvider**: 主题系统，支持宿主页面继承
- **ResizableLayout**: 响应式布局，支持动态尺寸调整

### 安全架构
- **CSP 头**: 严格的 Content Security Policy 配置
- **Token 管理**: 安全的认证 Token 传递和存储
- **消息验证**: postMessage 消息的来源和完整性验证
- **沙箱模式**: iframe sandbox 属性限制权限

### 性能优化策略
- **代码分割**: 按功能模块动态加载
- **懒加载**: 非关键组件延迟加载
- **虚拟滚动**: 大量数据的高效渲染
- **缓存策略**: 智能缓存减少重复请求

## Implementation Strategy

### 开发阶段划分
1. **基础架构阶段** (2.5周): 搭建项目结构，实现核心组件
2. **AI 交互阶段** (3周): 集成 AI SDK，开发聊天功能
3. **集成优化阶段** (2.5周): 性能优化，测试，部署

### 风险缓解措施
- **技术风险**: 采用成熟稳定的开源库，避免过度定制
- **兼容性风险**: 充分测试不同浏览器和设备
- **性能风险**: 建立性能监控和预警机制
- **安全风险**: 安全代码审查和渗透测试

### 测试策略
- **单元测试**: Jest + Testing Library 覆盖核心逻辑
- **集成测试**: Cypress 测试 Widget 嵌入场景
- **端到端测试**: Playwright 测试完整用户流程
- **性能测试**: Lighthouse + WebPageTest 性能基准测试

## Task Breakdown Preview

- [ ] **项目架构搭建**: 配置 Vite + TypeScript + shadcn/ui 开发环境
- [ ] **Widget 核心组件**: 实现容器、桥接、主题等基础组件
- [ ] **跨域通信系统**: 开发 postMessage 通信协议和消息验证
- [ ] **AI 交互界面**: 集成 Vercel AI SDK，实现聊天和消息组件
- [ ] **样式和主题系统**: 实现响应式设计和多主题支持
- [ ] **性能优化**: 代码分割、懒加载、虚拟滚动等优化
- [ ] **安全加固**: CSP 配置、Token 管理、沙箱隔离
- [ ] **测试和文档**: 完善测试套件和开发文档
- [ ] **部署和监控**: CI/CD 流程和性能监控系统

## Dependencies

### 必需依赖
- **后端 API**: 需要升级以支持 Vercel AI SDK
- **UI/UX 设计**: 需要提供设计规范和视觉稿
- **测试资源**: 需要测试设备和环境支持
- **部署资源**: 需要 CDN 和域名配置

### 外部依赖
- **Vercel AI SDK**: 核心 AI 交互框架
- **shadcn/ui**: UI 组件库
- **浏览器兼容性**: 主流浏览器的 API 支持
- **CDN 服务**: 静态资源分发

## Tasks Created
- [ ] #2 - 项目架构搭建 (parallel: false, depends_on: [])
- [ ] #3 - 跨域通信系统 (parallel: false, depends_on: [2])
- [ ] #4 - 样式和主题系统 (parallel: true, depends_on: [2])
- [ ] #5 - Widget 核心组件 (parallel: true, depends_on: [2, 3, 4])
- [ ] #6 - AI 交互界面 (parallel: true, depends_on: [2, 3, 4])
- [ ] #7 - 状态管理系统 (parallel: true, depends_on: [2, 3, 4])
- [ ] #8 - 性能优化 (parallel: true, depends_on: [2, 3, 4, 5, 6, 7])
- [ ] #9 - 安全加固 (parallel: true, depends_on: [2, 3, 4, 5, 6, 7])
- [ ] #10 - 测试和部署 (parallel: true, depends_on: [2, 3, 4, 5, 6, 7])

Total tasks: 9
Parallel tasks: 6
Sequential tasks: 3
Estimated total effort: 82 hours
## Success Criteria (Technical)

### 性能指标
- Widget 初始化时间 < 1秒
- 首屏渲染时间 < 1.5秒
- AI 响应延迟 < 500ms
- Widget 体积 < 500KB (gzipped)
- Lighthouse 性能评分 > 90

### 质量指标
- TypeScript 覆盖率 100%
- 单元测试覆盖率 > 80%
- E2E 测试覆盖率 > 90%
- 代码规范符合 ESLint + Prettier
- 组件文档覆盖率 100%

### 兼容性指标
- 支持所有主流浏览器最新版本
- 移动端浏览器兼容性 > 95%
- 不同网站的 iframe 安全策略兼容性
- 响应式设计适配各种屏幕尺寸

## Estimated Effort

### 时间估算
- **总工期**: 8周 (2.5 + 3 + 2.5)
- **关键路径**: Widget 核心组件 -> AI 交互 -> 性能优化
- **并行开发**: 可并行进行组件开发和后端集成

### 资源需求
- **前端开发**: 2名高级 React 开发工程师
- **UI/UX 设计**: 1名设计师参与设计规范制定
- **测试**: 1名测试工程师负责测试用例和执行
- **运维**: 1名运维工程师负责部署和监控

### 风险缓冲
- **技术风险缓冲**: 额外 1周应对技术难题
- **兼容性测试**: 预留 1周进行多环境测试
- **文档和培训**: 预留 0.5周完善文档
