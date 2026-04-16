import modules from "../data/modules.json";

export function getModules() {
  return modules;
}

export function getDefaultModule() {
  return modules[0] || null;
}
