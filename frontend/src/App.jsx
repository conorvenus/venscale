import { useState, useEffect } from 'react'
import { ToastContainer, toast } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

function App() {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [deploymentId, setDeploymentId] = useState('')
  const [status, setStatus] = useState('')

  function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1)
  }

  useEffect(() => {
    if (!deploymentId) return

    const interval = setInterval(async () => {
      const response = await fetch(`/api/status?id=${deploymentId}`)
      const data = await response.json()
      setStatus(data.status)
      if (data.status === 'failed' || data.status === 'deployed') {
        setStatus('')
        setUrl('')
        clearInterval(interval)
      }
      if (data.status === 'deployed') {
        window.open(`http://${deploymentId}.pawsitter.site`, '_blank')
        toast.success('Your repository has been deployed successfully.', { autoClose: 5000 })
      }
      if (data.status === 'failed') {
        toast.error('An error occurred while deploying your repository.', { autoClose: 5000 })
        setError('An error occurred while deploying your repository.')
      }
    }, 2000)
  }, [deploymentId])

  async function deploy() {
    if (!url) return setError('Please enter a valid GitHub repository URL.')

    const response = await fetch(`/api/deploy?repoUrl=${url}`)
    if (!response.ok) {
      toast.error('You can only deploy a repository once every 10 seconds.', { autoClose: 5000 })
      return setError('You can only deploy a repository once every 10 seconds.')
    }

    const data = await response.json()
    setDeploymentId(data.id)
    setStatus('uploading')
  }

  return (
    <>
      <div className="w-screen h-screen grid place-items-center">
        <div className="absolute top-0 z-[-2] h-screen w-screen bg-neutral-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.3),rgba(255,255,255,0))]"></div>
        <div className="shadow-2xl shadow-blue-500/20 p-16 rounded-lg border-white text-white font-medium border-white/10 border w-fit flex flex-col gap-4">
          <div>
            <h1 className="text-lg">Deploy Your GitHub Repository</h1>
            <p className="font-extralight text-slate-300/50 text-sm">Enter your GitHub repository URL below to deploy it to <span className="font-medium text-slate-300/75">VenScale.</span></p>
          </div>
          <div className="flex flex-col gap-4">
            <input type="text" value={url} onChange={(event) => { setUrl(event.target.value); setError('') }} placeholder="https://github.com/username/repo" className="w-full mt-4 p-2 rounded-lg bg-slate-800/10 border border-white/10 placeholder:text-white/30 text-white outline-none" />
            <button onClick={deploy} disabled={status} className={`${!status ? 'bg-slate-800/10' : 'bg-slate-500/20'} text-white p-2 rounded-lg border border-white/10 w-full font-black`}>{status ? capitalize(status) + '...' : 'Deploy'}</button>
            {error && <p className="font-extralight text-slate-300/50 text-sm">{error}</p>}
          </div>
        </div>
      </div>
      <ToastContainer position='bottom-right' theme='dark' />
    </>
  )
}

export default App