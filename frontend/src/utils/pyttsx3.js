/**
 * pyttsx3 工具函数
 * 使用后端pyttsx3服务进行文本转语音
 */

const PYTTsx3_URL = '/api/tts/pyttsx3'

/**
 * 调用pyttsx3 API生成语音
 * @param {string} text - 要转换的文本
 * @param {number} rate - 语速，默认150
 * @param {number} volume - 音量，0-1.0
 * @returns {Promise<Blob>} - 返回音频Blob
 */
export async function pyttsx3(text, rate = 150, volume = 1.0) {
  try {
    // 构建请求体（使用默认语音，不选择男女声）
    const requestBody = {
      text: text,
      rate: rate,
      volume: volume
    }

    // 发送请求
    const response = await fetch(PYTTsx3_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      throw new Error(`pyttsx3 API请求失败: ${response.status} ${response.statusText}`)
    }

    // 获取音频数据
    const audioBlob = await response.blob()
    return audioBlob
  } catch (error) {
    console.error('pyttsx3调用失败:', error)
    throw error
  }
}

/**
 * 播放pyttsx3生成的音频
 * @param {Blob} audioBlob - 音频Blob对象
 * @param {Function} onEnd - 播放结束回调
 * @returns {HTMLAudioElement} - 音频元素
 */
export function playPyttsx3(audioBlob, onEnd = null) {
  const audioUrl = URL.createObjectURL(audioBlob)
  const audio = new Audio(audioUrl)
  
  if (onEnd) {
    audio.onended = () => {
      onEnd()
      URL.revokeObjectURL(audioUrl)
    }
  }
  
  audio.play()
  return audio
}

/**
 * 停止pyttsx3播放
 * @param {HTMLAudioElement} audio - 音频元素
 */
export function stopPyttsx3(audio) {
  if (audio) {
    audio.pause()
    audio.currentTime = 0
  }
}
