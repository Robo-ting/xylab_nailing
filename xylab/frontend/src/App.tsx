import { HashRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Calibration } from './pages/Calibration'
import { Perception } from './pages/Perception'
import { Intake } from './pages/Intake'
import { Planning } from './pages/Planning'
import { RuleBase } from './pages/RuleBase'
import { DecisionMatrix } from './pages/DecisionMatrix'
import { AgentConsole } from './pages/AgentConsole'
import { RobotControl } from './pages/RobotControl'
import { DigitalTwin } from './pages/DigitalTwin'
import { LogsReports } from './pages/LogsReports'

export function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/calibration" element={<Calibration />} />
          <Route path="/perception" element={<Perception />} />
          <Route path="/intake" element={<Intake />} />
          <Route path="/planning" element={<Planning />} />
          <Route path="/rulebase" element={<RuleBase />} />
          <Route path="/matrix" element={<DecisionMatrix />} />
          <Route path="/agent" element={<AgentConsole />} />
          <Route path="/robot" element={<RobotControl />} />
          <Route path="/twin" element={<DigitalTwin />} />
          <Route path="/logs" element={<LogsReports />} />
        </Route>
      </Routes>
    </HashRouter>
  )
}
