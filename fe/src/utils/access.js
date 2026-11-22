export const canOperate = (user) => ['operator', 'admin'].includes(user?.role);
