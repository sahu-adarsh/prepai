'use client';

import { Calendar, TrendingUp, Clock, Award } from 'lucide-react';

interface InterviewSession {
  sessionId: string;
  interviewType: string;
  candidateName: string;
  createdAt: string;
  status: 'active' | 'completed';
  overallScore?: number;
  duration?: number;
  recommendation?: string;
}

interface InterviewHistoryProps {
  sessions: InterviewSession[];
  onSessionClick?: (sessionId: string) => void;
}

export default function InterviewHistory({ sessions, onSessionClick }: InterviewHistoryProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      time: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      year: date.getFullYear()
    };
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600 bg-green-50';
    if (score >= 6) return 'text-blue-600 bg-blue-50';
    if (score >= 4) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const sortedSessions = [...sessions].sort((a, b) =>
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center space-x-2 mb-6">
        <Calendar className="w-6 h-6 text-gray-700" />
        <h2 className="text-2xl font-bold text-gray-900">Interview History</h2>
      </div>

      {sessions.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No interview history yet</p>
          <p className="text-sm text-gray-400 mt-2">Complete an interview to see it here</p>
        </div>
      ) : (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200"></div>

          <div className="space-y-6">
            {sortedSessions.map((session, index) => {
              const { date, time, year } = formatDate(session.createdAt);

              return (
                <div
                  key={session.sessionId}
                  onClick={() => onSessionClick?.(session.sessionId)}
                  className={`relative pl-20 ${
                    onSessionClick ? 'cursor-pointer hover:bg-gray-50 -mx-4 px-4 py-2 rounded-lg transition-colors' : ''
                  }`}
                >
                  {/* Timeline dot */}
                  <div className="absolute left-6 top-2 w-5 h-5 rounded-full bg-white border-4 border-blue-500 z-10"></div>

                  {/* Date badge */}
                  <div className="absolute left-0 top-0 text-right w-16">
                    <div className="text-sm font-bold text-gray-900">{date}</div>
                    <div className="text-xs text-gray-500">{year}</div>
                  </div>

                  {/* Content card */}
                  <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-gray-900 text-lg">
                          {session.interviewType}
                        </h3>
                        <p className="text-sm text-gray-600 mt-1">{session.candidateName}</p>
                      </div>

                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          session.status === 'completed'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-yellow-100 text-yellow-700'
                        }`}
                      >
                        {session.status}
                      </span>
                    </div>

                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <div className="flex items-center space-x-1">
                        <Clock className="w-4 h-4" />
                        <span>{time}</span>
                      </div>

                      {session.duration && (
                        <div className="flex items-center space-x-1">
                          <Clock className="w-4 h-4" />
                          <span>{Math.round(session.duration / 60)} min</span>
                        </div>
                      )}

                      {session.overallScore !== undefined && (
                        <div className="flex items-center space-x-1">
                          <Award className="w-4 h-4" />
                          <span className={`font-semibold ${getScoreColor(session.overallScore)}`}>
                            {session.overallScore.toFixed(1)}/10
                          </span>
                        </div>
                      )}
                    </div>

                    {session.recommendation && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="flex items-center space-x-2">
                          <TrendingUp className="w-4 h-4 text-gray-500" />
                          <span className="text-sm text-gray-600">
                            Recommendation:
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            {session.recommendation.replace(/_/g, ' ')}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}